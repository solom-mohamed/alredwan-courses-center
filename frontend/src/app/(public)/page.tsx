export const dynamic = "force-dynamic";

import ActivitiesSection from "@/components/landing-page/ActivitiesSection";
import CallToActionSection from "@/components/landing-page/CallToActionSection";
import CoursesSection from "@/components/landing-page/CoursesSection";
import GoalsSection from "@/components/landing-page/GoalsSection";
import HeroSection from "@/components/landing-page/HeroSection";
import InstructorsSection from "@/components/landing-page/InstructorsSection";
import StatisticsSection from "@/components/landing-page/StatisticsSection";
import TestimonialsSection from "@/components/landing-page/TestimonialsSection";
import VideosSection from "@/components/landing-page/VideosSection";
import WhatsAppWidget from "@/components/landing-page/WhatsAppWidget";
import WhyUsSection from "@/components/landing-page/WhyUsSection";

export default async function Home() {
  return (
    <main className="tablet:[&>section]:p-12 md:tablet:[&>section]:p-28 mobile-lg:[&>section]:px-6! md:mobile-lg:[&>section]:px-15! desktop-sm:[&>section]:px-32 lg:desktop-sm:[&>section]:px-80 laptop:[&>section]:px-24 lg:laptop:[&>section]:px-60 [&_h2>span]:text-beige-500 overflow-x-hidden px-6 py-12 md:px-16 md:py-28 lg:px-32 xl:px-64 [&>section]:py-12 md:[&>section]:py-28">
      <HeroSection />
      <StatisticsSection />
      <WhyUsSection />
      <InstructorsSection />
      <GoalsSection />
      <ActivitiesSection />
      <VideosSection />
      <CoursesSection />
      <TestimonialsSection />
      <CallToActionSection />
      <WhatsAppWidget />
    </main>
  );
}
