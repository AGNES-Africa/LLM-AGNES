import dynamic from 'next/dynamic';
//const SunburstChart = dynamic(() => import('./components/sunburst_new'), {ssr: false})
import SunburstChart from './components/sunburst_new'

export default function Home() {
  return (
      <div className="mt-1">
        <SunburstChart/>
      </div>
  );
}