"use client"

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'
import { Button } from './ui/button'
import { ThemeToggle } from './ui/theme-toggle'

export default function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false)

  const scrollToSection = (id: string) => {
    setIsMobileMenuOpen(false)
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-solid border-gray-200 dark:border-gray-800 bg-white/90 dark:bg-gray-950/90 backdrop-blur-sm">
      <div className="container flex h-16 items-center">
        {/* Left - Logo */}
        <div className="flex-shrink-0">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🐰</span>
            <span className="text-xl font-bold">Find My Bun</span>
          </Link>
        </div>

        {/* Center - Navigation Links */}
        <div className="hidden md:flex flex-grow justify-center items-center gap-8">
          <button
            onClick={() => scrollToSection('features')}
            className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
          >
            Features
          </button>
          <button
            onClick={() => scrollToSection('pricing')}
            className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
          >
            Pricing
          </button>
          <button
            onClick={() => scrollToSection('success-stories')}
            className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
          >
            Success Stories
          </button>
        </div>

        {/* Right - Buttons */}
        <div className="hidden md:flex items-center gap-4 flex-shrink-0">
          <ThemeToggle />
          <Link href="/login">
            <Button 
              variant="ghost" 
              className="hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Sign In
            </Button>
          </Link>
          <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank">
            <Button className="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
              Apply Now
            </Button>
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden ml-auto"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 dark:border-gray-800">
          <div className="container py-4 space-y-4">
            <button
              onClick={() => scrollToSection('features')}
              className="block w-full text-left text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Features
            </button>
            <button
              onClick={() => scrollToSection('pricing')}
              className="block w-full text-left text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Pricing
            </button>
            <button
              onClick={() => scrollToSection('success-stories')}
              className="block w-full text-left text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400"
            >
              Success Stories
            </button>
            <div className="pt-4 flex flex-col gap-2">
              <div className="flex justify-start mb-2">
                <ThemeToggle />
              </div>
              <Link href="/login" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="ghost" className="w-full justify-start hover:text-indigo-600 dark:hover:text-indigo-400">
                  Sign In
                </Button>
              </Link>
              <Link 
                href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" 
                target="_blank" 
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Button className="w-full justify-start bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
                  Apply Now
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}