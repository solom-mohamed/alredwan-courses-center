import { format } from "date-fns";
import { ar } from "date-fns/locale";
import Link from "next/link";
import Avatar from "@/components/ui/Avatar";
import { toHindiDigits } from "@/lib/utils";
import type { InstructorDetail } from "@/types/entities/instructors";

interface InstructorProfileViewProps {
  instructor: InstructorDetail;
}

export default function InstructorProfileView({
  instructor,
}: InstructorProfileViewProps) {
  const formattedJoinDate = instructor.joined_date
    ? format(new Date(instructor.joined_date), "dd MMMM yyyy", { locale: ar })
    : "غير متوفر";

  return (
    <div className="bg-white/40 backdrop-blur-md border border-white/20 rounded-3xl p-24 max-[1000px]:p-12 shadow-sm flex flex-col md:flex-row gap-24 max-[1000px]:flex-col max-[1000px]:gap-16">
      {/* Profile Image & Essential Info */}
      <div className="flex flex-col items-center gap-16 shrink-0">
        <Avatar
          src={instructor.image_url}
          alt={instructor.name}
          className="h-44 w-44 border-4 border-olive-100 shadow-md"
        />
        <div className="text-center">
          <h2 className="text-3xl font-medad text-olive-700">
            {instructor.name}
          </h2>
          <span className="text-olive-300 text-lg font-medium">
            {instructor.type_display}
          </span>
        </div>
      </div>

      {/* Detailed Info */}
      <div className="flex-1 flex flex-col gap-20">
        <div className="grid grid-cols-1 md:grid-cols-2 max-[1000px]:grid-cols-1 gap-16 max-[1000px]:gap-12">
          <InfoItem
            label="رقم الهاتف"
            value={toHindiDigits(instructor.phone || "")}
          />
          <InfoItem
            label="البريد الإلكتروني"
            value={instructor.email || "غير متوفر"}
          />
          <InfoItem
            label="تاريخ الانضمام"
            value={toHindiDigits(formattedJoinDate)}
          />
          <InfoItem
            label="عدد التقييمات"
            value={toHindiDigits((instructor.rating_count || 0).toString())}
          />
        </div>

        <div className="border-t border-olive-100/50 pt-16">
          <h4 className="text-xl font-bold text-olive-600 mb-8">
            النبذة الشخصية
          </h4>
          <p className="text-gray-700 leading-relaxed text-lg">
            {instructor.bio || "لا توجد نبذة شخصية متاحة حالياً لهذا المعلم."}
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-16 mt-16 pt-16 border-t border-olive-100/50">
          <div className="flex flex-wrap gap-8">
            {instructor.tags.map((tag) => (
              <span
                key={tag.id}
                className="bg-olive-50 text-olive-700 px-12 py-4 rounded-full text-sm font-medium border border-olive-100"
              >
                {tag.name}
              </span>
            ))}
          </div>

          <Link
            href={`/dashboard/all-attendances?instructor=${instructor.id}`}
            className="inline-flex items-center justify-center w-full md:w-auto max-[1000px]:w-full gap-8 bg-olive-600 text-white px-20 py-10 rounded-xl hover:bg-olive-700 transition-colors font-bold shadow-sm"
          >
            عرض سجل الحضور الكامل
          </Link>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-4">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className="text-gray-800 font-medium text-lg">{value}</span>
    </div>
  );
}
