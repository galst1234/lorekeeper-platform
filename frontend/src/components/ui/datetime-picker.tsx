import { Calendar, ChevronLeft, ChevronRight, Clock } from "lucide-react";
import { type CSSProperties, forwardRef, type HTMLAttributes, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface DateTimePickerProps extends Omit<HTMLAttributes<HTMLDivElement>, "onBlur" | "onChange"> {
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  name?: string;
  disabled?: boolean;
}

const weekdayLabels = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const calendarGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(7, minmax(0, 1fr))",
} satisfies CSSProperties;

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

function monthLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
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

type MonthDay = {
  key: string;
  date: Date | null;
};

function buildMonthDays(month: Date): MonthDay[] {
  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const firstDay = new Date(year, monthIndex, 1);
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const days: MonthDay[] = Array.from({ length: firstDay.getDay() }, (_, dayOffset) => ({
    key: `leading-${year}-${monthIndex}-${dayOffset}`,
    date: null,
  }));

  for (let day = 1; day <= daysInMonth; day += 1) {
    days.push({
      key: `${year}-${monthIndex}-${day}`,
      date: new Date(year, monthIndex, day),
    });
  }

  while (days.length % 7 !== 0) {
    days.push({
      key: `trailing-${year}-${monthIndex}-${days.length}`,
      date: null,
    });
  }

  return days;
}

export const DateTimePicker = forwardRef<HTMLButtonElement, DateTimePickerProps>(
  (
    {
      value,
      onChange,
      onBlur,
      name,
      disabled,
      className,
      id,
      "aria-describedby": ariaDescribedBy,
      "aria-invalid": ariaInvalid,
      ...props
    },
    ref
  ) => {
    const rootRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const { date, time } = splitDateTime(value);
    const selectedDate = useMemo(() => (date ? new Date(`${date}T${time}`) : null), [date, time]);
    const [visibleMonth, setVisibleMonth] = useState(() =>
      selectedDate ? new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1) : new Date()
    );
    const monthDays = useMemo(() => buildMonthDays(visibleMonth), [visibleMonth]);
    const today = toDateValue(new Date());

    useEffect(() => {
      if (selectedDate) {
        setVisibleMonth(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
      }
    }, [selectedDate]);

    useEffect(() => {
      if (!open) return;

      function handlePointerDown(event: PointerEvent) {
        if (!rootRef.current?.contains(event.target as Node)) {
          setOpen(false);
          onBlur?.();
        }
      }

      function handleKeyDown(event: KeyboardEvent) {
        if (event.key === "Escape") {
          setOpen(false);
          onBlur?.();
        }
      }

      document.addEventListener("pointerdown", handlePointerDown);
      document.addEventListener("keydown", handleKeyDown);

      return () => {
        document.removeEventListener("pointerdown", handlePointerDown);
        document.removeEventListener("keydown", handleKeyDown);
      };
    }, [onBlur, open]);

    function changeMonth(offset: number) {
      setVisibleMonth((current) => new Date(current.getFullYear(), current.getMonth() + offset, 1));
    }

    function selectDate(nextDate: Date) {
      onChange(combineDateTime(toDateValue(nextDate), time));
    }

    function selectToday() {
      const now = new Date();
      const nextValue = combineDateTime(toDateValue(now), `${pad(now.getHours())}:${pad(now.getMinutes())}`);
      onChange(nextValue);
      setVisibleMonth(now);
    }

    return (
      <div ref={rootRef} className={cn("relative", className)} {...props}>
        <Button
          id={id}
          ref={ref}
          type="button"
          variant="outline"
          className={cn("w-full justify-start px-3 font-normal", !date && "text-muted-foreground")}
          onClick={() => setOpen((current) => !current)}
          onBlur={onBlur}
          aria-describedby={ariaDescribedBy}
          aria-expanded={open}
          aria-haspopup="dialog"
          aria-invalid={ariaInvalid}
          disabled={disabled}
        >
          <Calendar data-icon="inline-start" />
          <span className="truncate">{formatDisplayValue(value)}</span>
        </Button>

        {open && (
          <div
            className="absolute left-0 top-full mt-2 w-80 max-w-full rounded-md border border-border bg-popover p-3 text-popover-foreground shadow-md"
            role="dialog"
            aria-label="Choose date and time"
          >
            <div className="flex items-center justify-between gap-2">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => changeMonth(-1)}
                aria-label="Previous month"
              >
                <ChevronLeft data-icon="inline" />
              </Button>
              <p className="text-sm font-medium">{monthLabel(visibleMonth)}</p>
              <Button type="button" variant="ghost" size="icon" onClick={() => changeMonth(1)} aria-label="Next month">
                <ChevronRight data-icon="inline" />
              </Button>
            </div>

            <div className="mt-3 gap-1 text-center text-xs text-muted-foreground" style={calendarGridStyle}>
              {weekdayLabels.map((weekday) => (
                <div key={weekday} className="py-1">
                  {weekday}
                </div>
              ))}
            </div>

            <div className="gap-1" style={calendarGridStyle}>
              {monthDays.map((day) => {
                const dayValue = day.date ? toDateValue(day.date) : "";
                const selected = dayValue && dayValue === date;
                const current = dayValue && dayValue === today;

                return day.date ? (
                  <Button
                    key={dayValue}
                    type="button"
                    variant={selected ? "default" : "ghost"}
                    size="icon"
                    className={cn("h-9 w-full", current && !selected && "border border-input")}
                    onClick={() => selectDate(day.date)}
                    aria-pressed={!!selected}
                  >
                    {day.date.getDate()}
                  </Button>
                ) : (
                  <div key={day.key} className="h-9" />
                );
              })}
            </div>

            <div className="mt-3 flex items-center gap-2">
              <Clock data-icon="inline-start" className="text-muted-foreground" />
              <Input
                type="time"
                name={name}
                value={time}
                onBlur={onBlur}
                onChange={(event) => onChange(combineDateTime(date || toDateValue(visibleMonth), event.target.value))}
                aria-label="Time"
                aria-invalid={ariaInvalid}
                disabled={disabled}
                step={60}
              />
            </div>

            <div className="mt-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-1">
                <Button type="button" variant="ghost" size="sm" onClick={selectToday}>
                  Today
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => onChange("")}>
                  Clear
                </Button>
              </div>
              <Button
                type="button"
                size="sm"
                onClick={() => {
                  setOpen(false);
                  onBlur?.();
                }}
              >
                Done
              </Button>
            </div>
          </div>
        )}
      </div>
    );
  }
);

DateTimePicker.displayName = "DateTimePicker";
