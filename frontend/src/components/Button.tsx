import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'xl' | 'icon';
  children: React.ReactNode;
}

const variantStyles = {
  primary: "bg-emerald-500 text-white hover:bg-emerald-600 focus:ring-emerald-500",
  secondary: "bg-gray-100 text-gray-800 border border-gray-200 hover:bg-gray-200 focus:ring-gray-300",
  outline: "border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 hover:border-gray-400 focus:ring-gray-300",
  ghost: "text-gray-500 hover:text-gray-900 hover:bg-gray-100 focus:ring-gray-300",
  danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  link: "text-emerald-600 underline-offset-4 hover:underline focus:ring-emerald-500",
};

const sizeStyles = {
  default: "h-10 px-5 text-sm",
  sm: "h-8 px-3 text-xs",
  lg: "h-12 px-8 text-sm",
  xl: "h-14 px-10 text-base",
  icon: "h-10 w-10",
};

export default function Button({
  variant = 'primary',
  size = 'default',
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-offset-0 focus:ring-offset-white disabled:pointer-events-none disabled:opacity-50 font-sans text-xs tracking-wide';

  return (
    <button
      className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
      {...props}
    >
      {children}
    </button>
  );
}
