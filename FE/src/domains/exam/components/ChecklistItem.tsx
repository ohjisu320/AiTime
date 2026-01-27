import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChecklistItemProps {
  label: string;
  isChecked: boolean;
  onToggle: () => void;
}

const ChecklistItem: React.FC<ChecklistItemProps> = ({ label, isChecked, onToggle }) => (
  <div 
    onClick={onToggle}
    className={cn(
      "self-stretch h-12 pl-4 pr-3 bg-gray-50 rounded-[10px] flex justify-start items-center gap-3 cursor-pointer transition-colors",
      isChecked ? "bg-green-50" : "hover:bg-gray-100"
    )}
  >
    <CheckCircle2 className={cn(
      "w-5 h-5 transition-colors",
      isChecked ? "text-green-500" : "text-gray-300"
    )} />
    <span className={cn(
      "text-base transition-colors",
      isChecked ? "text-gray-800 font-medium" : "text-gray-700"
    )}>
      {label}
    </span>
  </div>
);

export default ChecklistItem;