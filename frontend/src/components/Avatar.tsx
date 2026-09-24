import React, { useState } from 'react';

interface AvatarProps {
  src?: string | null;
  name: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  name,
  className = '',
  size = 'md'
}) => {
  const [hasError, setHasError] = useState(false);

  // Iniciais do nome parlamentar
  const getInitials = (n: string) => {
    if (!n) return 'CD';
    const parts = n.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-12 h-12 text-sm',
    lg: 'w-16 h-16 text-base',
    xl: 'w-24 h-24 text-xl',
  };

  if (!src || hasError) {
    return (
      <div
        className={`flex items-center justify-center rounded-full bg-slate-200 text-slate-700 font-semibold select-none ring-2 ring-white shrink-0 ${sizeClasses[size]} ${className}`}
        title={name}
      >
        {getInitials(name)}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={name}
      onError={() => setHasError(true)}
      className={`rounded-full object-cover ring-2 ring-white shrink-0 bg-slate-100 ${sizeClasses[size]} ${className}`}
      loading="lazy"
    />
  );
};
