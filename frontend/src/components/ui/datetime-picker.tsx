import { Calendar as CalendarIcon, Clock } from "lucide-react";
import { forwardRef, type HTMLAttributes, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface DateTimePickerProps extends Omit<HTMLAttributes<HTMLButtonElement>, "onBlur" | "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  name?: string;
  disabled?: boolean;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

function toDateValue(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function splitDateTime(value: string): { date: string; time: string } {
  const [date = "", time = ""] = value.split("T");
  return { date, time: time.slice(0, 5) || "00:00" };
}

function combineDateTime(date: string, time: string): string {
  if (!date) return "";
  return `${date}T${time || "00:00"}`;
}

function formatDisplayValue(value: string): string {
  const { date, time } = splitDateTime(value);
  if (!date) return "Select date and time";

  const parsed = new Date(`${date}T${time}`);
  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export const DateTimePicker = forwardRef<HTMLButtonElement, DateTimePickerProps>(
  ({ value, onChange, onBlur, name, disabled, className, id, ...props }, ref) => {
    const [open, setOpen] = useState(false);
    const { date, time } = splitDateTime(value);
    const selectedDate = useMemo(() => (date ? new Date(`${date}T${time}`) : undefined), [date, time]);

    function handleSelect(nextDate: Date | undefined) {
      onChange(nextDate ? combineDateTime(toDateValue(nextDate), time) : "");
    }

    function handleOpenChange(nextOpen: boolean) {
      setOpen(nextOpen);
      if (!nextOpen) onBlur?.();
    }

    return (
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <Button
            id={id}
            ref={ref}
            type="button"
            variant="outline"
            className={cn("w-full justify-start px-3 font-normal", !date && "text-muted-foreground", className)}
            disabled={disabled}
            {...props}
          >
            <CalendarIcon className="h-4 w-4" />
            <span className="truncate">{formatDisplayValue(value)}</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-3" align="start">
          <Calendar mode="single" selected={selectedDate} onSelect={handleSelect} autoFocus />
          <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
            <Clock className="h-4 w-4 shrink-0 text-muted-foreground" />
            <Input
              type="time"
              name={name}
              value={time}
              onChange={(event) => onChange(combineDateTime(date || toDateValue(new Date()), event.target.value))}
              aria-label="Time"
              disabled={disabled}
              step={60}
            />
          </div>
        </PopoverContent>
      </Popover>
    );
  }
);

DateTimePicker.displayName = "DateTimePicker";
