import VideoShowcase from "@/components/landing-page/VideoShowcase";
import ScrollReveal from "@/components/ui/ScrollReveal";
import { landingVideos } from "@/dev-data/videos";

export default function VideosSection() {
  return (
    <section
      id="videos"
      className="container-wide tablet:px-12! mobile-lg:px-6! bg-[linear-gradient(180deg,#FFF_0%,#EEF2EC_100%)]"
    >
      <ScrollReveal
        direction="up"
        className="flex w-full flex-col items-center"
      >
        <div className="title-block">
          <h2>
            شاهد <span>الواحة</span> عن قرب
          </h2>
          <p>
            مقاطع قصيرة من داخل واحة الرضوان تنقل لك أجواء التعلم والأنشطة وقصص
            طلابنا
          </p>
        </div>
      </ScrollReveal>

      <ScrollReveal
        direction="up"
        delay={0.2}
        amount={0.1}
        className="flex w-full flex-col items-center"
      >
        <VideoShowcase videos={landingVideos} />
      </ScrollReveal>
    </section>
  );
}
