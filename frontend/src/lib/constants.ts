/**
 * Application-wide constants
 * Centralized for easy updates and consistency
 */

// Section 1: Book Demo
export const BOOK_DEMO = {
  headline: 'End-to-end AI copilot for PCB design, enabling robotics simulations at scale.',
  subheadline: 'Stop hunting datasheets and fighting footprints.',
  demoLink: 'Watch 90s demo',
  waitlistLink: 'Join our waitlist',
} as const

export const BADGES = [
  { text: 'Gradient Accelerator', href: 'https://gradient.build/' },
  { text: 'Pre-seed' },
  { text: 'Built at Princeton' },
  { text: 'Built by electrical engineers' },
] as const

// Section 2: PCB Co-Pilot
export const PCB_COPILOT = {
  title: 'PCB Co-Pilot',
  subtitle: 'End-to-end design process for PCB boards',
  description: 'Jigsaw works seamlessly with your existing development tools, acting as a copilot that understands component compatibility—not just keyword search.',
  steps: [
    {
      number: '01',
      title: 'Prompt or upload',
      description: [
        'Describe your circuit in natural language or upload existing project files. Jigsaw intelligently parses requirements and understands component relationships.',
        'Works seamlessly with any workflow, making it easy to get started regardless of your current design process.',
      ],
    },
    {
      number: '02',
      title: 'AI assembles compatible schematic & layout',
      description: [
        'Our multi-agent AI system selects compatible components based on electrical specifications and generates a complete schematic.',
        'Proposes optimized PCB layouts automatically, eliminating manual datasheet hunting and component compatibility guesswork.',
      ],
    },
    {
      number: '03',
      title: 'Simulate before you build',
      description: [
        'Run physics-aware simulations to catch overcurrent, thermal issues, and signal integrity problems before fabrication.',
        'Iterate virtually instead of physically, saving time and reducing costly design revisions.',
      ],
    },
    {
      number: '04',
      title: 'Verified BOM & one-click order',
      description: [
        'Receive a clean Bill of Materials with verified, in-stock parts from trusted suppliers.',
        'Order everything you need with a single click, eliminating the hassle of sourcing components across multiple vendors.',
      ],
    },
  ],
} as const

// Section 3: Large Scale Simulation Sandbox
export const SIMULATION_SANDBOX = {
  title: 'Large Scale Simulation Sandbox',
  subtitle: 'Abstraction-based simulation at scale',
  description: 'Our abstraction methodology enables robotics simulations at a fraction of the cost of traditional physics engines by modeling component behavior rather than simulating every physical interaction.',
  steps: [
    {
      title: 'Component verification',
      description: [
        'Once a component is verified to work correctly, its behavioral model is captured.',
        'The model encodes state conditions, operational parameters, and functional capabilities.',
      ],
    },
    {
      title: 'Behavioral abstraction',
      description: [
        'Each component is represented by its behavioral model rather than full physics.',
        'Models communicate state transitions and capabilities without computational overhead.',
      ],
    },
    {
      title: 'Hierarchical composition',
      description: [
        'When components connect to form new systems, abstraction layers stack upward.',
        'Each level models system behavior rather than simulating every physical detail.',
      ],
    },
    {
      title: 'Robotics at scale',
      description: [
        'This abstraction enables complex robotics simulations in real-time.',
        'Achieves the same results at a fraction of the computational cost.',
      ],
    },
  ],
} as const

// Section 4: Industries We Disrupt
export const INDUSTRIES = [
  {
    name: 'Robotics & Drones',
    market: '$5T potential by 2050',
    pain: 'Months spent on sensor integration and power management. Each iteration requires new PCBs.',
  },
  {
    name: 'Electric Vehicles',
    market: 'Fastest growing automotive segment',
    pain: 'Complex power systems, safety-critical designs. Component compatibility issues cause costly delays.',
  },
  {
    name: 'Medical Devices',
    market: '$600B+ global market',
    pain: 'Regulatory compliance requires extensive documentation. Part availability issues delay FDA submissions.',
  },
  {
    name: 'Industrial IoT',
    market: '$1T+ by 2030',
    pain: 'High-volume, cost-sensitive designs. Engineers waste weeks optimizing BOMs and footprints.',
  },
  {
    name: 'Consumer Electronics',
    market: '$1.2T+ global market',
    pain: 'Rapid iteration cycles. Miniaturization requires perfect component selection and layout.',
  },
  {
    name: 'Aerospace & Defense',
    market: 'Mission-critical reliability',
    pain: 'Extreme reliability requirements. Component obsolescence and long lead times derail projects.',
  },
] as const

export const MARKET_OVERVIEW = {
  totalMarket: '$3.8B PCB design software market (2023)',
  growth: 'Growing to $11-12B by 2032 (12-14% CAGR)',
  opportunity: '1% market capture = $10M+ ARR. Long-term: $100M+ ARR potential',
} as const

// Section 4: Reach Out
export const REACH_OUT = {
  headline: 'Reach Out',
  email: 'contact.jigsaw.ai@gmail.com',
  bookingLink: 'https://calendar.app.google/vKCFkPPsfraoG79z9',
} as const

// Industry Professional Quotes
export const INDUSTRY_QUOTES = [
  {
    quote: 'Engineers waste an average of 68% of their time searching for parts, configuring and unnecessarily recreating new components.',
    author: 'Robert Lyons',
    title: 'Siemens',
  },
  {
    quote: 'A single part broke on our $50k robot, we had to shut down the lab since the manufacturer had updated their part.',
    author: 'Yixuan Huang',
    title: 'Princeton Postdoc',
  },
  {
    quote: 'There are substantial challenges in hardware/software interfaces because software is discrete while hardware interacts with the continuous world.',
    author: 'Vijay Kumar',
    title: 'Professor of Robotics @ University of Pennsylvania',
  },
  {
    quote: 'Two major pain points: lack of standardized communication protocols and poor or inconsistent documentation.',
    author: 'ARIA Research',
    title: 'UK Robotics Industry Report',
  },
  {
    quote: 'Global semiconductor shortages force design compromises, raise costs, and extend lead times.',
    author: 'Protolabs Manufacturing Report',
    title: 'Robotics Hardware Analysis',
  },
  {
    quote: 'Integrating components from multiple vendors faces obstacles due to lack of standardized protocols and inconsistent documentation.',
    author: 'Industry Survey',
    title: 'Robotics Integration Challenges',
  },
  {
    quote: 'The robot operating environment affects every hardware choice. IP ratings and chemical compatibility limit component selection.',
    author: 'Protolabs',
    title: 'Robotics Hardware Manufacturing Report',
  },
] as const

// Companies Who Care
export const COMPANIES_WHO_CARE = [
  {
    name: 'Air Force',
    logoPath: 'airforce_logo.png',
  },
  {
    name: 'Department of Defense',
    logoPath: 'dod_logo.png',
  },
  {
    name: 'Siemens',
    logoPath: 'siemens_logo.png',
  },
  {
    name: 'Gradient',
    logoPath: 'gradient_logo.svg',
  },
  {
    name: 'Princeton Electric Speedboating',
    logoPath: 'pes_logo.avif',
  },
] as const
