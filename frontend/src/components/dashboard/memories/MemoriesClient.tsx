"use client";

import { useState } from "react";
import { MemoryListItem } from "@/types/entities";
import MemoryCard from "./MemoryCard";
import MemoryUploadModal from "./MemoryUploadModal";
import Lightbox from "./Lightbox";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { getPrivateMemories, getGeneralMemories } from "@/actions/memories";
import Loader from "@/components/ui/Loader";

interface Props {
  initialMemories: MemoryListItem[];
  role: string;
}

export default function MemoriesClient({ initialMemories, role }: Props) {
  const [memories, setMemories] = useState<MemoryListItem[]>(initialMemories);
  const [activeTab, setActiveTab] = useState<"general" | "private">("general");
  const [loading, setLoading] = useState(false);
  
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const isSupervisor = role === "supervisor";
  const hasPrivateFeed = role === "parent" || role === "student";

  const fetchTabMemories = async (tab: "general" | "private") => {
    setLoading(true);
    setActiveTab(tab);
    try {
      if (tab === "general") {
        const data = await getGeneralMemories();
        setMemories(data);
      } else {
        const data = await getPrivateMemories();
        setMemories(data);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div className="flex gap-4">
          <Button 
            variant={activeTab === "general" ? "primary" : "secondary"}
            onClick={() => fetchTabMemories("general")}
          >
            الصور العامة
          </Button>
          {hasPrivateFeed && (
            <Button 
              variant={activeTab === "private" ? "primary" : "secondary"}
              onClick={() => fetchTabMemories("private")}
            >
              ذكرياتي الخاصة
            </Button>
          )}
        </div>
        
        {isSupervisor && (
          <Button onClick={() => setIsUploadModalOpen(true)}>
            إضافة ذكرى
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><Loader thickness="4px" /></div>
      ) : memories.length === 0 ? (
        <EmptyState 
          title="لا توجد ذكريات بعد" 
          description="لم يتم إضافة أي ذكريات في هذا القسم." 
        />
      ) : (
        <div className="flex flex-col gap-6">
          {memories.map((memory, index) => (
            <MemoryCard 
              key={memory.id} 
              memory={memory} 
              onClick={() => setLightboxIndex(index)} 
            />
          ))}
        </div>
      )}

      {lightboxIndex !== null && (
        <Lightbox 
          memories={memories} 
          initialIndex={lightboxIndex} 
          onClose={() => setLightboxIndex(null)}
          onMemoryDeleted={(id) => {
            setMemories(prev => prev.filter(m => m.id !== id));
            setLightboxIndex(null);
          }}
          isSupervisor={isSupervisor}
        />
      )}

      <MemoryUploadModal 
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={() => {
          setIsUploadModalOpen(false);
          fetchTabMemories(activeTab);
        }}
      />
    </div>
  );
}
