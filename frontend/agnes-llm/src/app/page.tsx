import dynamic from 'next/dynamic'
 
const SunburstChart = dynamic(() => import('./components/Sunburst'), {
  ssr: false,
})

export default function Home() {
  return (
      <div className="mt-1">
        <SunburstChart/> 
      </div> 
  );
}

