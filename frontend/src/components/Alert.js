import React from 'react';

export default function Alert({ children, variant = 'info' }) {
  const styles = {
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    error: 'bg-red-50 text-red-900 border-red-200',
    success: 'bg-emerald-50 text-emerald-900 border-emerald-200',
    warning: 'bg-amber-50 text-amber-900 border-amber-200',
  };

  return (
    <div className={`p-4 rounded-xl border ${styles[variant]} flex gap-3 items-start shadow-sm`}>
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}