# opencv를 사용하여 동영상에서 프레임을 추출하고 이미지로 저장합니다.
import cv2
import os


# 설치 확인
# 안 되어 있으면 설치하세요 (requirements.txt 참고)
print(cv2.__version__) # 4.13.0

def extract_frames(video_path, output_folder, interval=1): # 기본 interval=1 (모든 프레임 저장)
    """
    동영상에서 프레임을 추출하여 이미지로 저장하는 함수
    
    :param video_path: 동영상 파일 경로
    :param output_folder: 이미지를 저장할 폴더 경로
    :param interval: 저장 간격(ex. 1이면 모든 프레임, 30이면 30프레임마다 1장 저장)
    """
    # 0. output 폴더 확인 (없으면 만들고 시작.)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f" 👶 폴더 생성: {output_folder}")

    # 1. 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(video_path)
    
    # 비디오 파일이 정상적으로 열리는지 확인
    if not cap.isOpened():
        print(" 👶 Error: 동영상 파일을 열 수 없습니다.")
        return

    # 비디오 메타데이터 확인
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # 총 프레임 수
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) # 가로 해상도 
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) # 세로 해상도
    fps = cap.get(cv2.CAP_PROP_FPS) # 초당 프레임 수

    print(f" 👶 비디오 정보 - 전체 프레임 수: {length}, 해상도: {width}x{height}, FPS: {fps}")

    frame_count = 0 # 현재 프레임
    saved_count = 0 # 저장된 프레임 수
    # 참고 length : 총 프레임 수

    print(" 👶 프레임 추출 시작...")

    while True: 
        # 3. 프레임 읽기
        ret, frame = cap.read()

        if not ret:
            break  # 더 이상 프레임이 없으면 종료

        # 4. interval 고려해서 프레임을 이미지 파일로 저장 (파일명: frame_00000.jpg 형태)
        if frame_count % interval == 0: # 각 interval 마다
            frame_filename = os.path.join(output_folder, f"frame_{saved_count:05d}.jpg")
            cv2.imwrite(frame_filename, frame)
            saved_count += 1
            # 진행 상황 표시(100 프레임마다)
            if saved_count % 100 == 0:
                print(f"현재 {saved_count} / {length} 프레임 저장됨...")

        frame_count += 1

    # 5. 자원 해제
    cap.release()
    print(f" 👶 프레임 추출 완료! 총 {saved_count}프레임이 '{output_folder}'폴더에 저장되었습니다.")


if __name__ == "__main__":
    video_path = "sample_video.mp4"  # 처리할 비디오 파일 경로
    output_folder = "extracted_frames"  # 프레임을 저장할 폴더
    interval = 1  # 예: 1 프레임마다 1장 저장 (1초에 30프레임인 경우 매초 30장 저장)

    extract_frames(video_path, output_folder, interval)

    

    


