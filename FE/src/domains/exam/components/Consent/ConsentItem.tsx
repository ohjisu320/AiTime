import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConsentItemProps {
  icon: React.ReactNode;
  title: string;
  isChecked: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const ConsentItem: React.FC<ConsentItemProps> = ({ icon, title, isChecked, onToggle, children }) => (
  <div
    onClick={onToggle}
    className={cn(
      "group relative p-4 rounded-xl border-2 transition-all cursor-pointer",
      isChecked ? "border-[#6366F1] bg-indigo-50/30" : "border-gray-100 hover:border-gray-200 shadow-sm"
    )}
  >
    <div className="flex items-center gap-3 mb-2">
      <div className={cn(
        "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
        isChecked ? "bg-white shadow-sm text-[#6366F1]" : "bg-gray-50 text-gray-400"
      )}>
        {icon}
      </div>
      <h3 className="text-base font-bold text-gray-800 flex-grow text-left">{title}</h3>
      <div className={cn(
        "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all",
        isChecked ? "bg-[#6366F1] border-[#6366F1]" : "border-gray-300 group-hover:border-gray-400"
      )}>
        {isChecked && <Check className="w-4 h-4 text-white stroke-[3]" />}
      </div>
    </div>
    <div className="ml-11 text-left">{children}</div>
  </div>
);

export default ConsentItem;