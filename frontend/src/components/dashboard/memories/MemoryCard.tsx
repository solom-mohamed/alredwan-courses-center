import { MemoryListItem } from "@/types/entities";
import { getFullImageUrl } from "@/lib/image-utils";
import Image from "next/image";
import { formatDate } from "@/lib/utils";
import Avatar from "@/components/ui/Avatar"; // Assuming you have this

interface Props {
  memory: MemoryListItem;
  onClick: () => void;
}

export default function MemoryCard({ memory, onClick }: Props) {
  const imageUrl = getFullImageUrl(memory.thumbnail_url || memory.file_url) || "";
  
  return (
    <div 
      className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden mb-6"
    >
      {/* Post Header */}
      <div className="flex items-center gap-3 p-4">
        {/* Placeholder avatar based on first letter or use a default one */}
        <div className="h-10 w-10 rounded-full bg-olive-100 flex items-center justify-center text-olive-700 font-bold shrink-0">
          {memory.uploader_name ? memory.uploader_name[0] : "م"}
        </div>
        <div className="flex flex-col">
          <span className="font-semibold text-gray-900 text-sm">
            {memory.uploader_name || "مستخدم غير معروف"}
          </span>
          <span className="text-xs text-gray-500">
            {formatDate(memory.created_at)}
          </span>
        </div>
      </div>

      {/* Post Media */}
      <div 
        className="relative w-full bg-black flex items-center justify-center cursor-pointer max-h-[600px] min-h-[300px]"
        onClick={onClick}
      >
        <Image 
          src={imageUrl} 
          alt={memory.caption || "Memory"} 
          width={800}
          height={600}
          className="object-contain w-full h-auto max-h-[600px]"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 70vw, 50vw"
        />
        
        {memory.media_type === "video" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 transition-colors hover:bg-black/40">
            <div className="w-16 h-16 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center shadow-lg transform transition-transform hover:scale-110">
              <div className="w-0 h-0 border-t-[10px] border-t-transparent border-l-[16px] border-l-gray-900 border-b-[10px] border-b-transparent ml-2" />
            </div>
          </div>
        )}
      </div>
      
      {/* Post Footer / Description */}
      {memory.caption && (
        <div className="p-4">
          <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
            <span className="font-semibold ml-2">{memory.uploader_name}</span>
            {memory.caption}
          </p>
        </div>
      )}
    </div>
  );
}
