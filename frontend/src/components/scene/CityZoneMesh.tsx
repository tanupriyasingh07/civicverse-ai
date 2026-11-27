import { useMemo, useState } from 'react';
import { Html } from '@react-three/drei';
import type { InfrastructureAsset, RiskLevel, ZoneState } from '../../types/simulation';

interface CityZoneMeshProps {
  zone: ZoneState;
  assets: InfrastructureAsset[];
  isSelected: boolean;
  onSelect: (zoneId: string) => void;
}

const RISK_COLORS: Record<RiskLevel, { base: string; emissive: string; badge: string }> = {
  LOW: { base: '#10b981', emissive: '#059669', badge: 'bg-emerald-500/90 text-slate-950' },
  MODERATE: { base: '#eab308', emissive: '#ca8a04', badge: 'bg-amber-400/90 text-slate-950' },
  HIGH: { base: '#f97316', emissive: '#ea580c', badge: 'bg-orange-500/95 text-white' },
  CRITICAL: { base: '#ef4444', emissive: '#dc2626', badge: 'bg-red-600/95 text-white' },
};

export function CityZoneMesh({ zone, assets, isSelected, onSelect }: CityZoneMeshProps) {
  const [hovered, setHovered] = useState(false);
  const palette = RISK_COLORS[zone.risk_level] || RISK_COLORS.LOW;

  // Deterministic procedural building blocks per zone
  const buildings = useMemo(() => {
    const seedNum = zone.zone_id.charCodeAt(zone.zone_id.length - 1);
    const cols = 3;
    const rows = 3;
    const list: { x: number; z: number; w: number; d: number; h: number; isTall: boolean }[] = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = r * cols + c;
        const hash = ((seedNum * 17 + idx * 31) % 100) / 100;
        if (hash > zone.building_density + 0.15) continue;

        const offsetX = (c - 1) * 4.8;
        const offsetZ = (r - 1) * 4.8;
        const isCommercial = zone.zone_type === 'commercial' || zone.zone_type === 'medical_district';
        const baseH = isCommercial ? 3.5 + hash * 6.5 : 1.6 + hash * 3.8;

        list.push({
          x: offsetX,
          z: offsetZ,
          w: 2.8 + (hash % 0.8),
          d: 2.8 + ((1 - hash) % 0.8),
          h: baseH,
          isTall: baseH > 5.5,
        });
      }
    }
    return list;
  }, [zone.zone_id, zone.building_density, zone.zone_type]);

  const totalAssignedUnits =
    zone.assigned_resources.water_tankers +
    zone.assigned_resources.medical_units +
    zone.assigned_resources.cooling_units;

  return (
    <group position={[zone.grid_x, 0, zone.grid_z]}>
      {/* Base Zone Heat-Risk Slab */}
      <mesh
        position={[0, 0.2, 0]}
        receiveShadow
        onClick={(e) => {
          e.stopPropagation();
          onSelect(zone.zone_id);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry args={[zone.width, 0.4, zone.depth]} />
        <meshStandardMaterial
          color={palette.base}
          emissive={palette.emissive}
          emissiveIntensity={isSelected ? 0.55 : hovered ? 0.35 : 0.18}
          roughness={0.45}
          metalness={0.2}
        />
      </mesh>

      {/* Selection Highlight Border */}
      {(isSelected || hovered) && (
        <mesh position={[0, 0.45, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[zone.width * 0.62, zone.width * 0.67, 4]} />
          <meshBasicMaterial color={isSelected ? '#38bdf8' : '#e2e8f0'} />
        </mesh>
      )}

      {/* Procedural Urban Buildings */}
      {buildings.map((b, i) => (
        <mesh
          key={i}
          position={[b.x, 0.4 + b.h / 2, b.z]}
          castShadow
          receiveShadow
          onClick={(e) => {
            e.stopPropagation();
            onSelect(zone.zone_id);
          }}
        >
          <boxGeometry args={[b.w, b.h, b.d]} />
          <meshStandardMaterial
            color={b.isTall ? '#334155' : '#1e293b'}
            emissive={palette.emissive}
            emissiveIntensity={0.08}
            roughness={0.35}
            metalness={0.65}
          />
        </mesh>
      ))}

      {/* Infrastructure Beacon Towers (Hospitals / Water / Fire / Cooling) */}
      {assets.map((asset, idx) => {
        const beaconColor =
          asset.asset_type === 'hospital'
            ? '#38bdf8'
            : asset.asset_type === 'water_station'
            ? '#06b6d4'
            : asset.asset_type === 'emergency_station'
            ? '#f43f5e'
            : '#a855f7';
        return (
          <group key={asset.asset_id} position={[-6 + idx * 4, 0.4, 6.2]}>
            <mesh position={[0, 2.5, 0]}>
              <cylinderGeometry args={[0.35, 0.55, 5, 12]} />
              <meshStandardMaterial color={beaconColor} emissive={beaconColor} emissiveIntensity={0.6} />
            </mesh>
            <mesh position={[0, 5.4, 0]}>
              <sphereGeometry args={[0.6, 16, 16]} />
              <meshBasicMaterial color={beaconColor} />
            </mesh>
          </group>
        );
      })}

      {/* Dispatched Resource Orb Indicator */}
      {totalAssignedUnits > 0 && (
        <mesh position={[6.2, 1.3, -6.2]}>
          <octahedronGeometry args={[0.85, 0]} />
          <meshStandardMaterial color="#38bdf8" emissive="#0284c7" emissiveIntensity={0.85} />
        </mesh>
      )}

      {/* Floating Tactical HUD Tag */}
      <Html position={[0, 7.2, 0]} center distanceFactor={65} zIndexRange={[10, 0]}>
        <button
          onClick={() => onSelect(zone.zone_id)}
          className={lex flex-col items-center rounded-md border px-2.5 py-1 text-left shadow-lg backdrop-blur-md transition }
        >
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-white">{zone.zone_id}</span>
            <span className={ounded px-1.5 py-0.2 text-[9px] font-extrabold }>
              {zone.risk_level}
            </span>
          </div>
          <span className="whitespace-nowrap text-[10px] font-medium text-slate-300">
            {zone.ambient_temp_c.toFixed(1)}°C • Risk {zone.risk_score.toFixed(0)}
          </span>
        </button>
      </Html>
    </group>
  );
}
