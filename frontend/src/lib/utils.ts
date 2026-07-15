import { cva } from "class-variance-authority";
import clsx from "clsx";
import { parse } from "date-fns";
import { ClassNameValue, twMerge } from "tailwind-merge";

export function cn(...inputs: ClassNameValue[]) {
  return twMerge(clsx(inputs));
}

export { cva };

/*
type HindiDigitsMode = "auto" | "string" | "number";

interface HindiDigitsOptions {
  mode?: HindiDigitsMode;
  decimals?: number;
  preserveLeadingZeros?: boolean;
}

// TODO(utils): Advanced version kept for later reuse.
export function toHindiDigits(
  num: number | string,
  options: HindiDigitsOptions = {},
): string {
  const westernToHindiDigits: Record<string, string> = {
    "0": "٠",
    "1": "١",
    "2": "٢",
    "3": "٣",
    "4": "٤",
    "5": "٥",
    "6": "٦",
    "7": "٧",
    "8": "٨",
    "9": "٩",
  };

  const { mode = "auto", decimals = 2, preserveLeadingZeros = false } = options;
  const isString = typeof num === "string";
  const raw = isString ? num : String(num);

  const hasLeadingZeros = isString && /^0\d+/.test(raw);
  const isIntegerString = isString && /^\d+$/.test(raw);
  const isDecimalString = isString && /^\d+\.\d+$/.test(raw);

  const useRawString =
    mode === "string" ||
    (mode === "auto" &&
      ((preserveLeadingZeros && hasLeadingZeros && isIntegerString) ||
        isDecimalString));

  const numberText = useRawString
    ? raw
    : Number.isInteger(+num)
      ? (+num).toFixed(0)
      : (+num).toFixed(decimals);

  return numberText.replace(
    /[0-9]/g,
    (digit) => westernToHindiDigits[digit] || digit,
  );
}
*/

export function toHindiDigits(
  num: number | string,
  preserveLeadingZeros: boolean = false,
): string {
  if (num === null || num === undefined || num === "" || isNaN(+num) && typeof num !== 'string') return "٠";
  
  let number = num;

  const westernToHindiDigits: Record<string, string> = {
    "0": "٠",
    "1": "١",
    "2": "٢",
    "3": "٣",
    "4": "٤",
    "5": "٥",
    "6": "٦",
    "7": "٧",
    "8": "٨",
    "9": "٩",
  };

  if (!preserveLeadingZeros && !isNaN(+num))
    number = Number.isInteger(+num) ? (+num).toFixed(0) : (+num).toFixed(2);

  return number
    .toString()
    .replace(/[0-9]/g, (digit) => westernToHindiDigits[digit] || digit);
}

export function formatDate(dateStr: Date | string) {
  const date = typeof dateStr === "string" ? new Date(dateStr) : dateStr;
  return date.toLocaleDateString("ar-EG", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export function formatTime(dateStr: string | Date | undefined) {
  if (!dateStr) return dateStr;

  const date =
    dateStr instanceof Date ? dateStr : parse(dateStr, "HH:mm:ss", new Date());

  return date
    .toLocaleTimeString("ar-EG", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })
    .replaceAll("م", "مـ")
    .replaceAll("ص", "صـ");
}

const WEEKDAYS = [
  "الأحد",
  "الإثنين",
  "الثلاثاء",
  "الأربعاء",
  "الخميس",
  "الجمعة",
  "السبت",
];

export function getWeekDay(num: number) {
  return WEEKDAYS[num];
}

export function getWeekDayIndex(weekday: string) {
  return WEEKDAYS.findIndex((w) => w === weekday);
}

export function debounceFn(fn: (...args: any[]) => any, delay: number) {
  let timerId: NodeJS.Timeout;

  return (...args: any[]) => {
    clearTimeout(timerId);
    timerId = setTimeout(() => fn(...args), delay);
  };
}

export function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function getArabicPlural(
  num: number,
  {
    singular,
    twofer,
    plural,
  }: { singular: string; twofer: string; plural: string },
) {
  let pl = singular;

  if (num === 2) pl = twofer;
  if (num >= 3 && num <= 10) pl = plural;

  return pl;
}

export function persistInLocalStorage<T>(
  fn: (value: T | ((prev: T) => T)) => void,
  key: string,
) {
  return function (arg: T | ((prev: T) => T)) {
    // console.log(arg);
    if (typeof arg === "function") {
      fn((prev: T) => {
        //eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
        const valueToSave = (arg as Function)(prev);

        try {
          localStorage.setItem(key, JSON.stringify(valueToSave));
        } catch (e) {
          console.error("Local Storage Unavailable! ", e);
        }

        return valueToSave;
      });
    } else {
      try {
        localStorage.setItem(key, JSON.stringify(arg));
      } catch (e) {
        console.error("Local Storage Unavailable! ", e);
      }

      fn(arg);
    }
  };
}
