import React from 'react';
import { useNavigate } from 'react-router-dom';
import ConsentHeader from '../components/ConsentHeader';
import MissionCard from '../components/MissionCard';
import MissionInfoBox from '../components/MissionSide/MissionInfoBox';
import ReportButton from '../components/MissionSide/ReportButton';

const MissionListPage: React.FC = () => {
    const navigate = useNavigate();

    // API 명세 (videoTasks) 대응 Mock 데이터
    const videoTasks = [
        { type: 'TASK1', title: '동작 모방', subTitle: 'Motor Imitation', desc: '손뼉치기, 만세 등 동작 따라하기', variant: 'pink', status: 'UPLOADED' },
        { type: 'TASK2', title: '발화 모방', subTitle: 'Vocal Imitation', desc: '아, 맘마 등 소리 따라하기', variant: 'purple', status: 'PENDING' },
        { type: 'TASK3', title: '비대면 호명반응', subTitle: 'Response (Behind)', desc: '등 뒤에서 이름 불렀을 때 반응 확인', variant: 'blue', status: 'PENDING' },
        { type: 'TASK4', title: '대면 호명반응', subTitle: 'Eye Contact Check', desc: '마주보고 불렀을 때 눈맞춤 확인', variant: 'emerald', status: 'PENDING' },
    ];

    const completedCount = videoTasks.filter(t => t.status === 'UPLOADED').length;
    const isAllDone = completedCount === videoTasks.length;

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-slate-100 pb-20">
            <ConsentHeader currentStep={3} totalSteps={3} />

            <main className="max-w-[1240px] mx-auto mt-32 px-6 flex flex-col items-center">
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">검사 선택</h1>
                    <p className="text-xl text-gray-500 font-medium">
                        촬영할 검사를 선택해주세요 (총 {videoTasks.length}개 검사를 완료해야 합니다)
                    </p>
                </div>

                <div className="flex gap-10 items-start w-full">
                    {/* 왼쪽: 미션 그리드 레이아웃 (2x2) */}
                    <div className="grid grid-cols-2 gap-8 flex-1">
                        {videoTasks.map((task) => (
                            <MissionCard
                                key={task.type}
                                title={task.title}
                                subTitle={task.subTitle}
                                description={task.desc}
                                variant={task.variant as 'pink' | 'purple' | 'blue' | 'emerald'}
                                status={task.status as 'PENDING' | 'UPLOADED'}
                                onClick={() => navigate(`/exam/recorder/${task.type.toLowerCase()}`)}
                            />
                        ))}
                    </div>

                    {/* 오른쪽: 안내 섹션 */}
                    <div className="w-[380px] flex flex-col gap-6 sticky top-32">
                        <MissionInfoBox />
                        <ReportButton isAllDone={isAllDone} onSend={() => alert('리포트가 성공적으로 전송되었습니다!')} />
                    </div>
                </div>
            </main>
        </div>
    );
};

export default MissionListPage; 