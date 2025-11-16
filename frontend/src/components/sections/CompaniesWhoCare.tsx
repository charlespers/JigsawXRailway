import { COMPANIES_WHO_CARE } from '@/lib/constants'
import dodLogo from '@/assets/dod_logo.png'
import airforceLogo from '@/assets/airforce_logo.png'
import siemensLogo from '@/assets/siemens_logo.png'
import gradientLogo from '@/assets/gradient_logo.svg'
import pesLogo from '@/assets/pes_logo.avif'

const logoMap: Record<string, string> = {
  'dod_logo.png': dodLogo,
  'airforce_logo.png': airforceLogo,
  'siemens_logo.png': siemensLogo,
  'gradient_logo.svg': gradientLogo,
  'pes_logo.avif': pesLogo,
}

export default function CompaniesWhoCare() {
  return (
    <div className="py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h3 className="text-sm font-mono uppercase tracking-wider text-gray-500 mb-2">
            Companies Who Care
          </h3>
        </div>
        
        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
          {COMPANIES_WHO_CARE.map((company) => (
            <div
              key={company.name}
              className="flex items-center justify-center opacity-60 hover:opacity-100 transition-opacity"
            >
              <img
                src={logoMap[company.logoPath]}
                alt={company.name}
                className="h-8 md:h-10 w-auto object-contain grayscale hover:grayscale-0 transition-all"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

