import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-blue-600 text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 hover:shadow-blue-700/40 hover:scale-105 focus:ring-blue-500",
        secondary:
          "bg-gray-100 text-gray-900 hover:bg-gray-200 hover:scale-105 focus:ring-gray-500",
        outline:
          "border-2 border-gray-300 bg-transparent hover:bg-gray-100 hover:border-gray-400 focus:ring-gray-500",
        ghost:
          "hover:bg-gray-100 hover:text-gray-900 focus:ring-gray-500",
        danger:
          "bg-red-600 text-white shadow-lg shadow-red-600/25 hover:bg-red-700 hover:shadow-red-700/40 hover:scale-105 focus:ring-red-500",
        link:
          "text-blue-600 underline-offset-4 hover:underline focus:ring-blue-500",
        success:
          "bg-green-600 text-white shadow-lg shadow-green-600/25 hover:bg-green-700 hover:shadow-green-700/40 hover:scale-105 focus:ring-green-500",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        xl: "h-14 rounded-xl px-10 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
