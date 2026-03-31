import { WindowsContainer, WindowsButton } from "../layout/WindowsLayout";

interface Props {
    onConfirm: () => void;
    onCancel: () => void;
}

export default function LogoutModal({ onConfirm, onCancel }: Props) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-[1px]">
            <WindowsContainer className="bg-[#d4d0c8] !border-[#d4d0c8] !border-4 !border-t-white !border-l-white !border-r-[#404040] !border-b-[#404040] p-1 w-[300px] shadow-2xl relative">
                {/* Title Bar */}
                <div className="bg-[#000080] px-2 py-1 flex justify-between items-center mb-4">
                    <span className="text-white font-bold text-[13px] tracking-wide">시스템 종료</span>
                    <button
                        onClick={onCancel}
                        className="w-[16px] h-[14px] bg-[#d4d0c8] border border-white border-r-[#404040] border-b-[#404040] flex items-center justify-center text-[10px] leading-none active:border-inset"
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div className="flex flex-col items-center gap-6 px-4 py-2 mb-2">
                    <div className="flex items-center gap-4 w-full">
                        <div className="w-[32px] h-[32px] shrink-0 grayscale">
                            <img
                                src="/icons/shutdown.png"
                                alt=""
                                className="w-full h-full object-contain"
                                onError={(e) => {
                                    e.currentTarget.style.display = 'none';
                                    e.currentTarget.parentElement!.innerText = '🔑';
                                    e.currentTarget.parentElement!.style.fontSize = '24px';
                                    e.currentTarget.parentElement!.style.textAlign = 'center';
                                }}
                            />
                        </div>
                        <div className="text-[13px]">
                            <p>시스템을 종료하고 로그아웃 하시겠습니까?</p>
                        </div>
                    </div>

                    <div className="flex gap-4 justify-center w-full">
                        <WindowsButton
                            onClick={onConfirm}
                            className="w-[80px] hover:bg-[#e0e0e0] active:scale-[0.98]"
                        >
                            예(Y)
                        </WindowsButton>
                        <WindowsButton
                            onClick={onCancel}
                            className="w-[80px] hover:bg-[#e0e0e0] active:scale-[0.98]"
                        >
                            아니오(N)
                        </WindowsButton>
                    </div>
                </div>
            </WindowsContainer>
        </div>
    );
}
