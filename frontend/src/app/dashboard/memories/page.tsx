import { getGeneralMemories } from "@/actions/memories";
import { getUser } from "@/actions/auth";
import MemoriesClient from "@/components/dashboard/memories/MemoriesClient";

export default async function MemoriesPage() {
  const [initialMemories, user] = await Promise.all([
    getGeneralMemories(),
    getUser()
  ]);

  return (
    <div className="px-16 py-26">
      <div className="font-medad text-olive-300 mb-15 flex flex-col gap-10 text-6xl">
        <span className="text-olive-700">السلام عليكم</span>
        <span>ذكريات المسجد</span>
      </div>

      <MemoriesClient initialMemories={initialMemories} role={user.role} />
    </div>
  );
}
