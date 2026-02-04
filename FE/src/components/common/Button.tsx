import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      default: 'bg-primary text-primary-foreground hover:bg-secondary-foreground shadow-lg shadow-indigo-100',
      secondary: 'bg-gray-200 text-gray-500 hover:bg-gray-300',
      outline: 'border-2 border-gray-200 bg-transparent hover:bg-gray-50 text-gray-600',
      ghost: 'bg-transparent hover:bg-gray-100 text-gray-500',
    };

    const sizes = {
      sm: 'h-10 px-4 text-sm',
      md: 'h-12 px-6 text-base',
      lg: 'h-16 px-8 text-xl',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center rounded-2xl font-bold transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };