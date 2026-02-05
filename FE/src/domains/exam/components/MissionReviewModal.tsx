import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogOverlay,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { videoApi } from '@/domains/video/api/videoApi';
import Swal from 'sweetalert2';

interface MissionReviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    examId: string | null;
    videoId: string;
    onRetake: () => void;
    onDelete: () => void;
}

const MissionReviewModal: React.FC<MissionReviewModalProps> = ({
    isOpen,
    onClose,
    title,
    examId,
    videoId,
    onRetake,
    onDelete
}) => {
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // 🆕 모달이 열리거나 videoId가 변경될 때 videoUrl 초기화
    useEffect(() => {
        setVideoUrl(null);
    }, [videoId, isOpen]);

    // 🎥 영상 보기 핸들러
    const handleViewVideo = async () => {
        if (!examId || !videoId) return;
        try {
            setIsLoading(true);
            // videoId 사용
            const response = await videoApi.getVideoUrl(examId, videoId);
            setVideoUrl(response.viewUrl);
        } catch (error) {
            console.error(error);
            Swal.fire('오류', '영상을 불러오는데 실패했습니다.', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    // 🔄 재촬영 핸들러 (영상 삭제 후 촬영 페이지로 이동)
    const handleRetakeVideo = async () => {
        if (!examId || !videoId) return;

        try {
            setIsLoading(true);
            await videoApi.deleteVideo(examId, videoId);
            onRetake(); // 상위 컴포넌트에서 페이지 이동 처리
        } catch (error) {
            console.error(error);
            Swal.fire('오류', '영상 삭제 중 문제가 발생했습니다.', 'error');
            setIsLoading(false);
        }
    };

    // 🗑️ 삭제 핸들러 (영상 삭제 후 리스트 갱신)
    const handleDeleteVideo = async () => {
        if (!examId || !videoId) return;

        try {
            setIsLoading(true);
            await videoApi.deleteVideo(examId, videoId);
            onDelete(); // 상위 컴포넌트에서 리스트 갱신 처리
        } catch (error) {
            console.error(error);
            Swal.fire('오류', '영상 삭제 중 문제가 발생했습니다.', 'error');
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogOverlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />

            <DialogContent className="fixed left-[50%] top-[50%] z-50 w-full max-w-[480px] translate-x-[-50%] translate-y-[-50%] rounded-3xl p-0 bg-white shadow-2xl border-none outline-none overflow-hidden">

                {/* ❌ 중복 X 버튼 제거됨 (DialogContent에 내장됨) */}

                <div className="p-8 pb-6 text-center">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-bold text-gray-900 mb-2">
                            {title} 완료
                        </DialogTitle>
                        <p className="text-gray-500">
                            촬영된 영상을 확인하거나 다시 촬영할 수 있습니다.
                        </p>
                    </DialogHeader>

                    {/* 비디오 플레이어 영역 */}
                    <div className="mt-6 w-full aspect-video bg-gray-100 rounded-xl overflow-hidden flex items-center justify-center relative">
                        {isLoading ? (
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-purple"></div>
                        ) : videoUrl ? (
                            <video
                                src={videoUrl}
                                controls
                                className="w-full h-full object-contain bg-black"
                                autoPlay
                            />
                        ) : (
                            <div className="text-gray-400 flex flex-col items-center gap-2">
                                <span className="text-5xl">🎬</span>
                                <span className="text-sm">영상을 확인해보세요</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* 하단 버튼 영역 */}
                <div className="p-6 bg-gray-50 flex flex-col gap-3">
                    {/* 1. 영상 보기 (비디오 없을 때만 표시) */}
                    {!videoUrl && (
                        <Button
                            onClick={handleViewVideo}
                            className="w-full h-12 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-lg shadow-md"
                        >
                            영상 보기
                        </Button>
                    )}

                    {/* 경고 문구 (항상 표시) */}
                    <p className="text-xs text-rose-500 text-center font-medium mt-2 mb-2">
                        ※ 재촬영 혹은 삭제 시 기존 영상은 복구할 수 없습니다.
                    </p>

                    <div className="flex gap-2">
                        {/* 2. 재촬영 */}
                        <Button
                            onClick={handleRetakeVideo}
                            disabled={isLoading}
                            variant="outline"
                            className="flex-1 h-12 border-2 border-indigo-100 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 font-bold rounded-xl"
                        >
                            {isLoading ? "..." : "재촬영"}
                        </Button>

                        {/* 3. 삭제 */}
                        <Button
                            onClick={handleDeleteVideo}
                            disabled={isLoading}
                            variant="outline"
                            className="flex-1 h-12 border-2 border-red-100 bg-red-50 text-red-600 hover:bg-red-100 font-bold rounded-xl"
                        >
                            삭제
                        </Button>

                    </div>
                </div>

            </DialogContent>
        </Dialog>
    );
};

export default MissionReviewModal;
