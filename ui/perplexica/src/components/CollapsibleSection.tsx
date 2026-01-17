import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CollapsibleSectionProps {
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
    className?: string;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
    title,
    children,
    defaultOpen = false,
    className,
}) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    if (!children) return null;

    return (
        <div className={cn('border border-light-200 dark:border-dark-200 rounded-lg overflow-hidden', className)}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center justify-between w-full p-4 bg-light-secondary dark:bg-dark-secondary hover:bg-light-secondary/80 dark:hover:bg-dark-secondary/80 transition-colors"
            >
                <h3 className="text-black dark:text-white font-medium text-lg">{title}</h3>
                {isOpen ? (
                    <ChevronUp className="text-black/50 dark:text-white/50" size={20} />
                ) : (
                    <ChevronDown className="text-black/50 dark:text-white/50" size={20} />
                )}
            </button>

            {isOpen && (
                <div className="p-4 bg-white dark:bg-dark-primary border-t border-light-200 dark:border-dark-200">
                    {children}
                </div>
            )}
        </div>
    );
};

export default CollapsibleSection;
