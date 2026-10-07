import { format } from "date-fns";
import { Award, Calendar, Star, Users, CheckCircle2 } from "lucide-react";
import Image from "next/image";
import { notFound } from "next/navigation";
import { getOptionalUser } from "@/actions/auth";
import { getInstructorById } from "@/actions/user";
import InstructorProfile from "@/assets/instructor-profile.png";
import RatingsSection from "@/components/ratings/RatingsSection";
import { getPublicCannotRateReason } from "@/lib/rating-access";

export default async function InstructorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const [instructor, session] = await Promise.all([
    getInstructorById(id, true),
    getOptionalUser(),
  ]);

  if (!instructor) {
    notFound();
  }

  const joinedYear = instructor.joined_date
    ? format(new Date(instructor.joined_date), "yyyy")
    : "خبير";
  console.log(instructor);
  return (
    <div
      className="flex min-h-full flex-1 flex-col bg-gradient-to-b from-gray-50/50 to-white pb-24"
      dir="rtl"
    >
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-gray-100 bg-white">
        {/* Decorative background blur element */}
        <div className="pointer-events-none absolute -top-24 -left-24 h-96 w-96 rounded-full bg-olive-500/5 blur-3xl" />

        <div className="container mx-auto px-4 py-12 sm:px-6 lg:py-16">
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-12">
            {/* Instructor Image with Modern Frame */}
            <div className="flex justify-center lg:col-span-4">
              <div className="group relative h-64 w-64 overflow-hidden rounded-[2.5rem] shadow-xl ring-4 ring-olive-500/15 transition-all duration-300 hover:ring-olive-500/30 lg:h-80 lg:w-80">
                <Image
                  src={instructor.image_url || InstructorProfile}
                  alt={instructor.name}
                  fill
                  priority
                  sizes="(max-width: 768px) 256px, 320px"
                  className="object-cover object-top transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              </div>
            </div>

            {/* Instructor Info */}
            <div className="space-y-6 text-center lg:col-span-8 lg:text-right">
              <div className="space-y-3">
                {/* Tags / Specializations */}
                {instructor.tags && instructor.tags.length > 0 && (
                  <div className="flex flex-wrap justify-center gap-2 lg:justify-start">
                    {instructor.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center gap-1 rounded-full bg-olive-500/10 px-3.5 py-1 text-xs font-semibold text-olive-600 transition-colors hover:bg-olive-500/20"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}

                <h1 className="text-4xl font-black tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
                  {instructor.name}
                </h1>

                <p className="text-xl font-bold text-olive-600 lg:text-2xl">
                  {instructor.type_display}
                </p>
              </div>

              <p className="mx-auto max-w-3xl text-base leading-relaxed text-gray-600 lg:mx-0 lg:text-lg">
                {instructor.bio ||
                  "لا يوجد وصف متاح حالياً لهذا المعلم. تفقد الدورات والتقييمات أدناه لمعرفة المزيد."}
              </p>

              {/* Statistics Grid */}
              <div className="grid grid-cols-2 gap-4 pt-2 sm:grid-cols-4">
                <div className="flex flex-col items-center gap-1 rounded-2xl border border-gray-100 bg-gray-50/80 p-4 transition-all hover:bg-white hover:shadow-md lg:items-start">
                  <div className="flex items-center gap-2 font-bold text-amber-500">
                    <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
                    <span className="text-2xl font-extrabold">
                      {instructor.average_rating || "0.0"}
                    </span>
                  </div>
                  <span className="text-xs font-medium text-gray-500">
                    التقييم العام
                  </span>
                </div>

                <div className="flex flex-col items-center gap-1 rounded-2xl border border-gray-100 bg-gray-50/80 p-4 transition-all hover:bg-white hover:shadow-md lg:items-start">
                  <div className="flex items-center gap-2 font-bold text-blue-600">
                    <Users className="h-5 w-5" />
                    <span className="text-2xl font-extrabold">
                      {instructor.rating_count || 0}
                    </span>
                  </div>
                  <span className="text-xs font-medium text-gray-500">
                    إجمالي المراجعات
                  </span>
                </div>

                <div className="flex flex-col items-center gap-1 rounded-2xl border border-gray-100 bg-gray-50/80 p-4 transition-all hover:bg-white hover:shadow-md lg:items-start">
                  <div className="flex items-center gap-2 font-bold text-purple-600">
                    <Calendar className="h-5 w-5" />
                    <span className="text-2xl font-extrabold">
                      {joinedYear}
                    </span>
                  </div>
                  <span className="text-xs font-medium text-gray-500">
                    سنة الانضمام
                  </span>
                </div>

                <div className="flex flex-col items-center gap-1 rounded-2xl border border-gray-100 bg-gray-50/80 p-4 transition-all hover:bg-white hover:shadow-md lg:items-start">
                  <div className="flex items-center gap-2 font-bold text-emerald-600">
                    <Award className="h-5 w-5" />
                    <span className="text-2xl font-extrabold">خبير</span>
                  </div>
                  <span className="text-xs font-medium text-gray-500">
                    المستوى الاكاديمي
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ratings Section */}
      <section className="container mx-auto mt-12 flex-1 px-4 sm:px-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            آراء الطلاب والمراجعات
          </h2>
          <p className="text-sm text-gray-500">
            تعرف على تجارب الطلاب الآخرين مع هذا المعلم
          </p>
        </div>

        <RatingsSection
          type="instructor"
          id={id}
          showForm={session?.role === "student" || session?.role === "parent"}
          courseId={undefined}
          cannotRateReason={getPublicCannotRateReason(session?.role)}
        />
      </section>
    </div>
  );
}
