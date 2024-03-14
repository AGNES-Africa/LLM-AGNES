import dynamic from 'next/dynamic';
const AgnesSunburstChart = dynamic(() => import('./components/sunburst'), {ssr: false})

export default function Home() {
  return (
    <div>
      <AgnesSunburstChart/>
    </div>
  );
}