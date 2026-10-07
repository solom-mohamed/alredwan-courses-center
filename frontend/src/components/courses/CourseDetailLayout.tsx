import { Pencil } from "lucide-react";
import Image, { type StaticImageData } from "next/image";
import type { ReactNode } from "react";
import CoursePurchaseModal from "@/components/courses/CoursePurchaseModal";
import RatingsSection from "@/components/ratings/RatingsSection";
import Button from "@/components/ui/Button";
import ImageLightbox from "@/components/ui/ImageLightbox";
import type { CourseEnrollmentState } from "@/lib/course-enrollment";
import { toHindiDigits } from "@/lib/utils";

const WHY_US_ITEMS = [
  "مناهج معتمدة ومبسطة",
  "معلمين ذوي خبرة عالية",
  "متابعة دورية وتقارير أداء",
  "بيئة تعليمية تفاعلية وآمنة",
];

export interface CourseDetailLayoutProps {
  /** Rendered above the content grid (e.g. `CourseHeader` or a title block). */
  header: ReactNode;
  imageSrc: string | StaticImageData;
  imageAlt: string;
  description: string;
  /** Optional content rendered under the description (e.g. tag chips). */
  descriptionExtra?: ReactNode;
  price: string;
  /** The enrollment call-to-action (modal or status button). */
  purchase: ReactNode;
  ratings: {
    type: "course" | "online_course";
    id: string;
    showForm: boolean;
    /** See `RatingsSection.cannotRateReason`. */
    cannotRateReason?: string;
  };
  backHref?: string;
}

export default function CourseDetailLayout({
  header,
  imageSrc,
  imageAlt,
  description,
  descriptionExtra,
  price,
  purchase,
  ratings,
  backHref = "/dashboard/courses",
}: CourseDetailLayoutProps) {
  return (
    <main className="h-full overflow-y-auto px-16 py-8 max-[1000px]:px-8">
      <div className="flex flex-col gap-8">
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <Button
            href={backHref}
            variant="secondary"
            size="small"
            className="shadow-soft w-fit border-none bg-white/60 px-10 backdrop-blur-sm"
          >
            العودة إلى كل الدورات
          </Button>
        </div>

        {header}

        {/* Content Grid */}
        <div className="grid grid-cols-[1.5fr_1fr] gap-12 max-[1000px]:grid-cols-1">
          {/* Left Column: Image & Details */}
          <div className="flex flex-col gap-10">
            <div className="shadow-soft relative aspect-video overflow-hidden rounded-[3rem] border-4 border-white/40">
              <ImageLightbox
                src={imageSrc}
                alt={imageAlt}
                className="absolute inset-0 h-full w-full"
              >
                <Image
                  src={imageSrc}
                  alt={imageAlt}
                  fill
                  sizes="(max-width: 1000px) 100vw, 60vw"
                  className="object-cover"
                  draggable="false"
                  priority
                />
              </ImageLightbox>
            </div>

            <div className="shadow-soft flex flex-col gap-6 rounded-[2.5rem] border border-white/60 bg-white/40 p-10 backdrop-blur-md max-[1000px]:p-6">
              <h2 className="text-olive-700 flex items-center gap-4 text-4xl font-bold">
                <Pencil size={24} className="text-olive-400" />
                عن الدورة
              </h2>
              <p className="text-2xl leading-relaxed break-words whitespace-pre-wrap text-gray-600">
                {description}
              </p>

              {descriptionExtra}
            </div>
          </div>

          {/* Right Column: Pricing & Purchase */}
          <div className="flex flex-col gap-10">
            <div className="shadow-soft flex flex-col gap-8 rounded-[2.5rem] border border-white/60 bg-white/40 p-10 backdrop-blur-md max-[1000px]:p-6">
              <div className="flex flex-col gap-2">
                <span className="text-xl text-gray-400">رسوم الدورة</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-olive-700 text-6xl font-bold">
                    {toHindiDigits(price)}
                  </span>
                  <span className="text-olive-500 text-2xl font-bold">
                    جنيه مصري
                  </span>
                </div>
              </div>

              <p className="text-xl text-gray-500 italic">
                احجز مكانك الآن واستفد من خصم الفترة المحدودة لطلاب الأكاديمية.
              </p>

              <div className="flex flex-col gap-4">
                {purchase}

                <Button
                  href="/contact-us"
                  variant="secondary"
                  className="w-full bg-white/80 py-6 text-3xl hover:bg-white"
                >
                  تواصل للاستفسار
                </Button>
              </div>
            </div>

            <div className="shadow-soft rounded-[2.5rem] border border-white/60 bg-white/40 p-10 backdrop-blur-md max-[1000px]:p-6">
              <h3 className="text-olive-700 mb-6 text-3xl font-bold">
                لماذا تختار الرضوان؟
              </h3>
              <ul className="space-y-4">
                {WHY_US_ITEMS.map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3 text-xl text-gray-600"
                  >
                    <div className="bg-olive-400 h-2 w-2 rounded-full" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Ratings Section */}
        <div className="shadow-soft mt-8 rounded-[3rem] border border-white/60 bg-white/40 p-10 backdrop-blur-md max-[1000px]:p-6">
          <h2 className="text-olive-700 mb-10 text-center text-4xl font-bold">
            تقييمات الدورة وآراء الطلاب
          </h2>
          <RatingsSection
            type={ratings.type}
            id={ratings.id}
            showForm={ratings.showForm}
            cannotRateReason={ratings.cannotRateReason}
          />
        </div>
      </div>
    </main>
  );
}

export function CourseDetailUnavailable({
  backHref = "/dashboard/courses",
}: {
  backHref?: string;
}) {
  return (
    <div className="flex h-full items-center justify-center px-16">
      <div className="shadow-soft rounded-[2.5rem_0] bg-gray-50 px-16 py-12 text-center">
        <h2 className="text-olive-500 mb-4 text-5xl font-bold">
          لم نتمكن من تحميل تفاصيل الدورة
        </h2>
        <Button href={backHref} size="small">
          العودة إلى الدورات
        </Button>
      </div>
    </div>
  );
}

/** The enrollment call-to-action for the `purchase` slot, driven by `getCourseEnrollmentState`. */
export function CoursePurchaseAction({
  enrollment,
  courseId,
  coursePrice,
  courseType,
}: {
  enrollment: CourseEnrollmentState;
  courseId: string;
  coursePrice: string;
  courseType: "physical" | "online";
}) {
  switch (enrollment.purchaseState) {
    case "enrolled":
      return (
        <Button className="w-full py-6 text-3xl" disabled>
          أنت مشترك بالفعل
        </Button>
      );
    case "pending":
      return (
        <Button className="w-full py-6 text-3xl" disabled>
          طلبك قيد المراجعة
        </Button>
      );
    case "enrollable":
      return (
        <CoursePurchaseModal
          role={enrollment.enrollmentRole}
          courseId={courseId}
          coursePrice={coursePrice}
          courseType={courseType}
          childrenOptions={enrollment.childrenOptions}
        />
      );
    default:
      return null;
  }
}
