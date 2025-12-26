'use client';

import { Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface YearFilterToggleProps {
  value: number | null;
  onChange: (minYear: number | null) => void;
}

const YEAR_OPTIONS = [
  { label: 'All Time', value: null },
  { label: 'Last 5Y', value: 2020 },
  { label: 'Last 3Y', value: 2022 },
  { label: 'Last 2Y', value: 2023 },
] as const;

export function YearFilterToggle({ value, onChange }: YearFilterToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <Calendar className="h-4 w-4 text-muted-foreground" />
      <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">
        Temporal Filter
      </span>
      <div className="flex gap-1">
        {YEAR_OPTIONS.map((option) => (
          <Button
            key={option.label}
            variant={value === option.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => onChange(option.value)}
            className="h-7 px-3 text-xs font-bold uppercase"
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
