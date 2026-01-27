// src/components/common/GlassBackButton.tsx
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  onClick: () => void;
  className?: string;
}

export const GlassBackButton = ({ onClick, className }: Props) => (
  <button
    onClick={onClick}
    className={cn(
      "absolute left-6 top-6 w-12 h-12 bg-white/20 hover:bg-white/30 rounded-full shadow-lg backdrop-blur-md flex items-center justify-center transition-all z-10",
      className
    )}
  >
    <ChevronLeft className="text-white w-6 h-6" strokeWidth={2} />
  </button>
);