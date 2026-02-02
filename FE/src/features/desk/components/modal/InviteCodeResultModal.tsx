import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

interface InviteCodeResultModalProps {
    isOpen: boolean;
    onClose: () => void;
    data: {
        inviteCode: string;
        childName: string;
        scheduledAt: string;
        parentPhone: string;
    } | null;
}

export default function InviteCodeResultModal({
    isOpen,
    onClose,
    data,
}: InviteCodeResultModalProps) {
    const [isCopied, setIsCopied] = useState(false);

    if (!isOpen || !data) return null;

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(data.inviteCode);
            setIsCopied(true);
            setTimeout(() => setIsCopied(false), 2000);
        } catch (err) {
            console.error("클립보드 복사 실패", err);
        }
    };

    // 날짜 포맷팅 (YYYY.MM.DD HH:mm)
    const formattedDate = new Date(data.scheduledAt).toLocaleString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-white w-full max-w-[420px] rounded-xl shadow-2xl overflow-hidden relative">
                <div className="pt-10 pb-6 text-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Check className="w-8 h-8 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800">
                        초대 코드가 발급되었습니다
                    </h2>
                    <p className="text-gray-500 mt-2">
                        보호자에게 초대 코드를 전달해주세요
                    </p>
                </div>

                <div className="px-8 pb-8 space-y-6">
                    {/* 초대 코드 표시 및 복사 영역 */}
                    <div className="bg-gray-50 rounded-lg p-5 border border-gray-200 flex flex-col items-center gap-3">
                        <span className="text-sm text-gray-500 font-medium">초대 코드</span>
                        <div className="flex items-center gap-3 w-full justify-between">
                            <span className="text-3xl font-mono font-bold text-[#5A55D6] tracking-wider w-full text-center">
                                {data.inviteCode}
                            </span>
                        </div>
                        <Button
                            onClick={handleCopy}
                            variant="outline"
                            size="sm"
                            className="w-full text-[#5A55D6] border-[#5A55D6] hover:bg-[#5A55D6]/5 flex items-center gap-2"
                        >
                            {isCopied ? (
                                <>
                                    <Check className="w-4 h-4" /> 복사 완료
                                </>
                            ) : (
                                <>
                                    <Copy className="w-4 h-4" /> 코드 복사하기
                                </>
                            )}
                        </Button>
                    </div>

                    {/* 환자 정보 요약 */}
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">환자 이름</span>
                            <span className="font-bold text-gray-700">{data.childName}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">예약 일시</span>
                            <span className="font-bold text-gray-700">{formattedDate}</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">연락처</span>
                            <span className="font-bold text-gray-700">{data.parentPhone.replace(/^(\d{2,3})(\d{3,4})(\d{4})$/, `$1-$2-$3`)}</span>
                        </div>
                    </div>

                    <Button
                        onClick={onClose}
                        className="w-full h-12 text-lg font-bold bg-[#5A55D6] hover:bg-[#4844b8] text-white rounded-lg transition-colors"
                    >
                        확인
                    </Button>
                </div>
            </div>
        </div>
    );
}
