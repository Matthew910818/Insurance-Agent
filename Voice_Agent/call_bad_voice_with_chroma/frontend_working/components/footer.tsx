import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="border-t border-solid border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="container py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-md bg-indigo-600 dark:bg-indigo-500 flex items-center justify-center">
                <span role="img" aria-label="bunny">🐰</span>
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400">
               Find My Bun
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Your AI-powered career companion connecting talented students with tech startups.
            </p>
            <div className="flex space-x-4">
              {['twitter', 'instagram', 'linkedin', 'github'].map((social) => (
                <Link 
                  href="#" 
                  key={social}
                  className="h-8 w-8 rounded-full border border-gray-200 dark:border-gray-800 flex items-center justify-center text-gray-500 dark:text-gray-400 hover:border-indigo-600 hover:text-indigo-600 dark:hover:border-indigo-400 dark:hover:text-indigo-400 transition-colors"
                >
                  <span className="sr-only">{social}</span>
                  <svg 
                    className="h-4 w-4" 
                    fill="currentColor" 
                    viewBox="0 0 24 24" 
                    aria-hidden="true"
                  >
                    {/* Simple placeholder icon */}
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-14v6h2v-6h-2zm0 8v2h2v-2h-2z"/>
                  </svg>
                </Link>
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-gray-900 dark:text-white">Product</h4>
            <ul className="space-y-3">
              <li>
                <Link href="/features" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Success Stories
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  For Startups
                </Link>
              </li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-gray-900 dark:text-white">Resources</h4>
            <ul className="space-y-3">
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Community
                </Link>
              </li>
              <li>
                <Link 
                  href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" 
                  target="_blank"
                  className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                >
                  Apply Now
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  FAQs
                </Link>
              </li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-gray-900 dark:text-white">Company</h4>
            <ul className="space-y-3">
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Team
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Contact
                </Link>
              </li>
              <li>
                <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Careers
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-10 border-t border-solid border-gray-200 dark:border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            &copy; {new Date().getFullYear()} Find My Bun. All rights reserved.
          </p>
          <div className="flex items-center gap-6 mt-4 md:mt-0">
            <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
              Privacy
            </Link>
            <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
              Terms
            </Link>
            <Link href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
              Cookies
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}