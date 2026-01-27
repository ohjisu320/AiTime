import React from 'react';
import { Check } from 'lucide-react';

const CardBadge: React.FC = () => (
  <div className="flex items-center justify-center w-10 h-10 bg-green-500 rounded-full shadow-lg">
    <Check className="w-6 h-6 text-white stroke-[3px]" />
  </div>
);

export default CardBadge;