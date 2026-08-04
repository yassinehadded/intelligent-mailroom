import { apiGet } from "@/lib/api-client";
import type {
  MaarchConnectionResponse,
  MaarchHealthResponse,
  MaarchReferenceResponse,
} from "@/types/api";

export interface MaarchEntitiesResponse {
  count: number;
  entities: Array<{
    id: string;
    serialId: number;
    shortLabel?: string;
    enabled?: boolean;
  }>;
}

export const maarchApi = {
  getHealth: () => apiGet<MaarchHealthResponse>("/api/v1/maarch/health"),
  getConnection: () => apiGet<MaarchConnectionResponse>("/api/v1/maarch/connection"),
  getEntities: () => apiGet<MaarchEntitiesResponse>("/api/v1/maarch/entities"),
  getReference: () => apiGet<MaarchReferenceResponse>("/api/v1/maarch/reference"),
};
