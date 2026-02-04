import { useState, useCallback, type ReactNode, type MouseEvent } from "react";

interface DraggableModalProps {
    children: ReactNode;
    initialWidth?: string;
    initialHeight?: string;
    onClose: () => void;
}

export function useDraggableModal() {
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

    const handleMouseDown = useCallback((e: MouseEvent<HTMLDivElement>) => {
        setIsDragging(true);
        setDragStart({
            x: e.clientX - position.x,
            y: e.clientY - position.y,
        });
    }, [position]);

    const handleMouseMove = useCallback((e: MouseEvent<HTMLDivElement>) => {
        if (!isDragging) return;
        setPosition({
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y,
        });
    }, [isDragging, dragStart]);

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
    }, []);

    return {
        position,
        isDragging,
        handleMouseDown,
        handleMouseMove,
        handleMouseUp,
    };
}

export default function DraggableModal({
    children,
    initialWidth = "80%",
    initialHeight = "80%",
    onClose,
}: DraggableModalProps) {
    const { position, isDragging, handleMouseDown, handleMouseMove, handleMouseUp } = useDraggableModal();

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={onClose}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
        >
            <div
                className="bg-[#d4d0c8] border-2 border-white border-r-[#404040] border-b-[#404040] p-1 flex flex-col shadow-xl"
                style={{
                    width: initialWidth,
                    height: initialHeight,
                    transform: `translate(${position.x}px, ${position.y}px)`,
                    cursor: isDragging ? "grabbing" : "default",
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* 드래그 가능한 타이틀바 영역은 children에서 처리 */}
                <div
                    className="contents"
                    onMouseDown={handleMouseDown}
                >
                    {children}
                </div>
            </div>
        </div>
    );
}
