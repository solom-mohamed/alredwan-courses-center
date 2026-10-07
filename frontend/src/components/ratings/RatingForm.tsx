"use client";

import { useEffect, useState } from "react";
import RatingStars from "@/components/shared/RatingStars";
import Button from "@/components/ui/Button";
import { toast } from "react-hot-toast";
import { Loader2, Send } from "lucide-react";
import {
  type InstructorRatingCourse,
  rateCourse,
  rateInstructor,
  rateOnlineCourse,
} from "@/actions/ratings";
import { getInstructorCourses } from "@/actions/courses";
import { getInstructorOnlineCourses } from "@/actions/online-courses";
import { cn } from "@/lib/utils";

interface RatingFormProps {
  type: "course" | "instructor" | "online_course";
  id: string | number;
  instructorId?: number; // Only for instructor rating
  courseId?: number; // Only for instructor rating
  onSuccess?: () => void;
  compact?: boolean;
}

const RatingForm: React.FC<RatingFormProps> = ({
  type,
  id,
  instructorId,
  courseId,
  onSuccess,
  compact = false,
}) => {
  const [rating, setRating] = useState<number>(10);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  // Physical and online courses share one <select>; values are prefixed
  // ("course:12" / "online:<uuid>") so the two id spaces don't collide.
  const [courses, setCourses] = useState<{ value: string; name: string }[]>(
    [],
  );
  const [selectedCourse, setSelectedCourse] = useState("");
  const [loadingCourses, setLoadingCourses] = useState(false);

  useEffect(() => {
    if (type === "instructor") {
      const fetchCourses = async () => {
        setLoadingCourses(true);
        try {
          const [physical, online] = await Promise.all([
            getInstructorCourses(String(id), { page_size: 100 }),
            getInstructorOnlineCourses(id),
          ]);
          const options = [
            ...physical.results.map((c) => ({
              value: `course:${c.id}`,
              name: c.name,
            })),
            ...online.map((c) => ({
              value: `online:${c.id}`,
              name: `${c.name} (دورة إلكترونية)`,
            })),
          ];
          setCourses(options);
          if (options.length > 0) {
            setSelectedCourse(options[0].value);
          }
        } catch (error) {
          console.error("Error fetching instructor courses:", error);
        } finally {
          setLoadingCourses(false);
        }
      };
      fetchCourses();
    }
  }, [type, id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      let result;
      if (type === "course") {
        result = await rateCourse(id, rating, feedback);
      } else if (type === "online_course") {
        result = await rateOnlineCourse(id as string, rating, feedback);
      } else {
        const finalInstructorId = instructorId || Number(id);
        const [kind, selectedId] = selectedCourse.split(":");
        const ratedCourse: InstructorRatingCourse | null = courseId
          ? { course: courseId }
          : kind === "online" && selectedId
            ? { online_course: selectedId }
            : kind === "course" && Number(selectedId)
              ? { course: Number(selectedId) }
              : null;
        if (!finalInstructorId || !ratedCourse) {
          toast.error("يرجى اختيار الدورة التدريبية");
          setLoading(false);
          return;
        }
        result = await rateInstructor(
          finalInstructorId,
          ratedCourse,
          rating,
          feedback,
        );
      }

      if (result.success) {
        toast.success(result.message);
        setFeedback("");
        if (onSuccess) onSuccess();
      } else {
        toast.error(result.message);
      }
    } catch {
      toast.error("حدث خطأ غير متوقع");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "border border-gray-100 bg-white shadow-xl",
        compact ? "space-y-4 rounded-2xl p-4" : "space-y-6 rounded-3xl p-8",
      )}
    >
      <div className="space-y-2 text-center">
        <h3
          className={cn(
            "font-bold text-gray-900",
            compact ? "text-2xl" : "mobile-lg:text-5xl text-4xl",
          )}
        >
          أضف تقييمك
        </h3>
        {!compact && (
          <p className="mobile-lg:text-2xl mt-2 text-xl text-gray-500">
            رأيك يهمنا ويساعدنا في التطوير
          </p>
        )}
      </div>

      {type === "instructor" && !courseId && (
        <div className="space-y-4">
          <label className="mr-1 text-2xl font-bold text-gray-700">
            الدورة التدريبية
          </label>
          {loadingCourses ? (
            <div className="flex items-center gap-2 py-3 text-xl text-gray-400">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>جاري تحميل الدورات...</span>
            </div>
          ) : (
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              required
              className="focus:ring-primary/20 focus:border-primary mt-2 w-full rounded-2xl border border-gray-200 bg-white p-6 text-2xl transition-all outline-none focus:ring-2"
            >
              <option value="" disabled>
                اختر الدورة
              </option>
              {courses.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      <div
        className={cn(
          "bg-primary/5 flex flex-col items-center rounded-2xl",
          compact ? "mt-2 gap-2 py-3" : "mt-4 gap-4 py-6",
        )}
      >
        <span
          className={cn(
            "text-primary font-medium",
            compact ? "text-lg" : "text-2xl",
          )}
        >
          التقييم العام (من 10)
        </span>
        <RatingStars
          rating={rating}
          editable
          size={compact ? "sm" : "lg"}
          onChange={setRating}
        />
        <span
          className={cn(
            "text-primary font-black",
            compact ? "mt-1 text-3xl" : "mobile-lg:text-5xl mt-2 text-4xl",
          )}
        >
          {rating}/10
        </span>
      </div>

      <div className={cn("space-y-2", compact ? "mt-4" : "mt-6 space-y-4")}>
        <label
          className={cn(
            "mr-1 font-bold text-gray-700",
            compact ? "text-lg" : "text-2xl",
          )}
        >
          ملاحظاتك (اختياري)
        </label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="اكتب تجربتك هنا..."
          className={cn(
            "focus:ring-primary/20 focus:border-primary mt-2 w-full resize-none rounded-2xl border border-gray-200 transition-all outline-none focus:ring-2",
            compact ? "min-h-[80px] p-4 text-lg" : "min-h-[120px] p-6 text-2xl",
          )}
        />
      </div>

      <Button
        type="submit"
        disabled={loading}
        className={cn(
          "shadow-primary/20 w-full gap-3 rounded-2xl font-bold shadow-lg",
          compact ? "mt-4 h-12 text-xl" : "mt-6 h-16 text-3xl",
        )}
      >
        {loading ? (
          <Loader2
            className={cn("animate-spin", compact ? "h-5 w-5" : "h-8 w-8")}
          />
        ) : (
          <>
            <Send className={compact ? "h-5 w-5" : "h-8 w-8"} />
            إرسال التقييم
          </>
        )}
      </Button>
    </form>
  );
};

export default RatingForm;
