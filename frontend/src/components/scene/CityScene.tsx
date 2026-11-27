import { Canvas } from '@react-three/fiber';
import { Grid, OrbitControls } from '@react-three/drei';
import type { CityState } from '../../types/simulation';
import { CityZoneMesh } from './CityZoneMesh';

interface CitySceneProps {
  city: CityState | null;
  selectedZoneId: string | null;
  onSelectZone: (zoneId: string) => void;
}

export function CityScene({ city, selectedZoneId, onSelectZone }: CitySceneProps) {
  return (
    <div className="relative h-full w-full bg-slate-950">
      <Canvas
        shadows
        camera={{ position: [0, 44, 52], fov: 45 }}
        onPointerMissed={() => onSelectZone('')}
      >
        <color attach="background" args={['#060b14']} />
        <fog attach="fog" args={['#060b14', 75, 165]} />

        <ambientLight intensity={0.65} />
        <directionalLight
          position={[35, 55, 25]}
          intensity={1.35}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <pointLight position={[-25, 20, -25]} intensity={0.45} color="#38bdf8" />

        {/* Urban Base Ground Plane */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]} receiveShadow>
          <planeGeometry args={[140, 140]} />
          <meshStandardMaterial color="#0b1220" roughness={0.9} />
        </mesh>

        {/* Arterial Road Network Strips */}
        {[-11, 11].map((pos) => (
          <group key={oads-}>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[pos, 0.01, 0]}>
              <planeGeometry args={[2.2, 82]} />
              <meshStandardMaterial color="#1e293b" />
            </mesh>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, pos]}>
              <planeGeometry args={[82, 2.2]} />
              <meshStandardMaterial color="#1e293b" />
            </mesh>
          </group>
        ))}

        <Grid
          position={[0, 0.02, 0]}
          args={[120, 120]}
          cellSize={4}
          cellThickness={0.5}
          cellColor="#1e293b"
          sectionSize={20}
          sectionThickness={1}
          sectionColor="#334155"
          fadeDistance={115}
        />

        {city?.zones.map((zone) => (
          <CityZoneMesh
            key={zone.zone_id}
            zone={zone}
            assets={city.infrastructure.filter((a) => a.zone_id === zone.zone_id)}
            isSelected={selectedZoneId === zone.zone_id}
            onSelect={onSelectZone}
          />
        ))}

        <OrbitControls
          enableDamping
          dampingFactor={0.07}
          maxPolarAngle={Math.PI / 2.15}
          minDistance={22}
          maxDistance={95}
        />
      </Canvas>

      {/* Bottom-Left 3D Legend Overlay */}
      <div className="pointer-events-none absolute bottom-4 left-4 flex flex-wrap items-center gap-3 rounded-lg border border-slate-800/90 bg-slate-950/85 px-3.5 py-2 text-xs backdrop-blur-md">
        <span className="font-semibold text-slate-400">Heat Risk:</span>
        <span className="flex items-center gap-1.5 text-emerald-400">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Low
        </span>
        <span className="flex items-center gap-1.5 text-amber-400">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" /> Moderate
        </span>
        <span className="flex items-center gap-1.5 text-orange-400">
          <span className="h-2.5 w-2.5 rounded-full bg-orange-500" /> High
        </span>
        <span className="flex items-center gap-1.5 text-red-400">
          <span className="h-2.5 w-2.5 rounded-full bg-red-600" /> Critical
        </span>
        <span className="mx-1 text-slate-700">|</span>
        <span className="flex items-center gap-1.5 text-sky-400">
          <span className="h-2.5 w-2.5 rotate-45 bg-sky-400" /> Dispatched Units
        </span>
      </div>
    </div>
  );
}
