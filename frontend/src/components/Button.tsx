import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'xl' | 'icon';
  children: React.ReactNode;
}

const variantStyles = {
  primary: "bg-white text-black hover:bg-gray-200 focus:ring-white",
  secondary: "bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-white/20 focus:ring-white",
  outline: "border border-white/20 bg-transparent text-white hover:bg-white/5 hover:border-white/40 focus:ring-white",
  ghost: "text-white/60 hover:text-white hover:bg-white/5 focus:ring-white",
  danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  link: "text-white underline-offset-4 hover:underline focus:ring-white",
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
  const baseStyles = 'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-offset-0 focus:ring-offset-black disabled:pointer-events-none disabled:opacity-50 font-mono text-xs tracking-wider uppercase';

  return (
    <button
      className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
      {...props}
    >
      {children}
    </button>
  );
}
