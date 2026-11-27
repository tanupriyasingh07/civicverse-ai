import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import type { InfrastructureAsset, RiskLevel, ZoneState } from '../../types/simulation';

interface CityZoneMeshProps {
  zone: ZoneState;
  assets: InfrastructureAsset[];
  isSelected: boolean;
  onSelect: (zoneId: string) => void;
}

const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: '#10b981',
  MODERATE: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
};

export function CityZoneMesh({ zone, assets, isSelected, onSelect }: CityZoneMeshProps) {
  const [hovered, setHovered] = useState(false);
  const beaconRef = useRef<THREE.Mesh>(null);
  const dispatchRef = useRef<THREE.Mesh>(null);

  const baseColor = RISK_COLORS[zone.risk_level] || '#38bdf8';

  const buildings = useMemo(() => {
    const cols = 3;
    const rows = 3;
    const list: Array<{ x: number; z: number; h: number; w: number; d: number }> = [];
    const seedVal = zone.zone_id.charCodeAt(1) * 17;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const hash = Math.sin(seedVal + r * 7 + c * 13) * 10000;
        const frac = hash - Math.floor(hash);
        const h = 0.7 + zone.building_density * 2.5 * (0.55 + frac * 0.85);
        const offsetX = ((c - 1) * zone.width) / 3.4;
        const offsetZ = ((r - 1) * zone.depth) / 3.4;
        list.push({
          x: offsetX,
          z: offsetZ,
          h,
          w: zone.width / 4.8,
          d: zone.depth / 4.8,
        });
      }
    }
    return list;
  }, [zone.zone_id, zone.building_density, zone.width, zone.depth]);

  const totalAssignedUnits =
    zone.assigned_resources.water_tankers +
    zone.assigned_resources.medical_units +
    zone.assigned_resources.cooling_units +
    zone.assigned_resources.emergency_personnel;

  const hasOverloadedAsset = assets.some(
    (a) => !a.operational || a.current_load > a.capacity
  );

  const dispatchScale = Math.min(2.2, 0.65 + totalAssignedUnits / 45);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (beaconRef.current) {
      beaconRef.current.rotation.y = t * 1.4;
      beaconRef.current.position.y = 3.2 + Math.sin(t * 2.4) * 0.14;
    }
    if (dispatchRef.current && totalAssignedUnits > 0) {
      dispatchRef.current.rotation.y = -t * 1.8;
    }
  });

  return (
    <group position={[zone.grid_x, 0, zone.grid_z]}>
      <mesh
        position={[0, 0.12, 0]}
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
        <boxGeometry args={[zone.width, 0.24, zone.depth]} />
        <meshStandardMaterial
          color={baseColor}
          emissive={baseColor}
          emissiveIntensity={isSelected ? 0.45 : hovered ? 0.3 : 0.15}
          roughness={0.55}
          metalness={0.2}
        />
      </mesh>

      {isSelected && (
        <mesh position={[0, 0.26, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[Math.max(zone.width, zone.depth) * 0.56, Math.max(zone.width, zone.depth) * 0.63, 32]} />
          <meshBasicMaterial color="#38bdf8" side={THREE.DoubleSide} />
        </mesh>
      )}

      {buildings.map((b, idx) => (
        <mesh
          key={idx}
          position={[b.x, 0.24 + b.h / 2, b.z]}
          castShadow
          receiveShadow
          onClick={(e) => {
            e.stopPropagation();
            onSelect(zone.zone_id);
          }}
        >
          <boxGeometry args={[b.w, b.h, b.d]} />
          <meshStandardMaterial
            color={isSelected ? '#e2e8f0' : '#475569'}
            emissive={baseColor}
            emissiveIntensity={0.14}
            roughness={0.45}
            metalness={0.35}
          />
        </mesh>
      ))}

      {assets.length > 0 && (
        <mesh ref={beaconRef} position={[0, 3.2, 0]}>
          <octahedronGeometry args={[0.32, 0]} />
          <meshStandardMaterial
            color={hasOverloadedAsset ? '#ef4444' : '#38bdf8'}
            emissive={hasOverloadedAsset ? '#dc2626' : '#0284c7'}
            emissiveIntensity={hasOverloadedAsset ? 1.1 : 0.75}
          />
        </mesh>
      )}

      {totalAssignedUnits > 0 && (
        <mesh
          ref={dispatchRef}
          position={[zone.width * 0.28, 1.35 * dispatchScale, zone.depth * 0.28]}
          scale={[dispatchScale, dispatchScale, dispatchScale]}
        >
          <cylinderGeometry args={[0.16, 0.34, 1.4, 8]} />
          <meshStandardMaterial
            color="#34d399"
            emissive="#10b981"
            emissiveIntensity={0.85}
          />
        </mesh>
      )}

      <Html position={[0, 4.1, 0]} center distanceFactor={28}>
        <div
          onClick={() => onSelect(zone.zone_id)}
          className={`cursor-pointer select-none whitespace-nowrap rounded-md border px-2 py-0.5 text-[10px] font-semibold shadow-lg backdrop-blur-sm transition ${
            isSelected
              ? 'border-sky-400 bg-slate-900/95 text-sky-200'
              : 'border-slate-700/80 bg-slate-950/85 text-slate-200 hover:border-slate-500'
          }`}
        >
          <span>{zone.zone_id}: {zone.name}</span>
          <span className="ml-1.5 font-mono text-[9px] text-amber-300">
            {zone.risk_score.toFixed(0)}
          </span>
          {totalAssignedUnits > 0 && (
            <span className="ml-1 rounded bg-emerald-500/20 px-1 font-mono text-[9px] text-emerald-300">
              +{totalAssignedUnits}u
            </span>
          )}
        </div>
      </Html>
    </group>
  );
}
