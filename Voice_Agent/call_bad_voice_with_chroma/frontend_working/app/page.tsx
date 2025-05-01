"use client"

import Link from 'next/link'
import { motion } from 'framer-motion'
import Navbar from '@/components/navbar'
import Footer from '@/components/footer'
import { Button } from '@/components/ui/button'
import { ArrowRight, CheckCircle, Sparkles, Users, Award, MessageSquare, Zap } from 'lucide-react'

export default function Home() {
  const fadeIn = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
      },
    },
  }

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden py-20 md:py-32 bg-gradient-to-br from-indigo-50 to-white dark:from-gray-900 dark:to-gray-950">
          <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] dark:opacity-[0.05]"></div>
          <div className="container px-4 md:px-6 relative">
            <div className="grid gap-10 lg:grid-cols-[1fr_400px] lg:gap-12 xl:grid-cols-[1fr_600px]">
              <motion.div
                className="flex flex-col justify-center space-y-6"
                initial="hidden"
                animate="visible"
                variants={fadeIn}
              >
                <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-white/30 dark:bg-gray-800/30 backdrop-blur-sm w-fit">
                  <span className="text-indigo-600 dark:text-indigo-400 mr-1">✨</span> 
                  Exclusive Community for Top Talent
                </div>
                <div className="space-y-4">
                  <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400">
                    Find My Bun
                  </h1>
                  <p className="max-w-[600px] text-gray-600 dark:text-gray-300 text-lg">
                    A platform that supercharges student careers using AI voice agents—think of it as a personal career assistant that works for you, not just another job board.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank">
                    <Button size="lg" className="group bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
                      Apply Now
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                  </Link>
                  <Link href="#features">
                    <Button size="lg" variant="outline" className="dark:text-white dark:border-gray-700">
                      Learn More
                    </Button>
                  </Link>
                </div>
                <div className="flex items-center space-x-3 pt-3">
                  <div className="flex -space-x-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-8 w-8 rounded-full border-2 border-white dark:border-gray-900 bg-indigo-600 overflow-hidden relative">
                        <div className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-white">
                          {String.fromCharCode(64 + i)}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Trusted by students from <span className="font-medium">Stanford</span>, <span className="font-medium">MIT</span>, <span className="font-medium">Berkeley</span>, and more
                  </div>
                </div>
              </motion.div>
              <motion.div
                className="flex items-center justify-center"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8 }}
              >
                <div className="relative h-[400px] w-full max-w-[500px] overflow-hidden rounded-xl border bg-white dark:bg-gray-950 p-1 shadow-2xl">
                  <div className="absolute inset-0 bg-gradient-to-tr from-indigo-100 via-white to-violet-100 dark:from-gray-900 dark:via-gray-950 dark:to-indigo-950 rounded-xl"></div>
                  <div className="absolute top-0 left-0 right-0 h-12 rounded-t-xl bg-white dark:bg-gray-900 flex items-center px-4 z-10 border-b">
                    <div className="flex space-x-2">
                      <div className="h-3 w-3 rounded-full bg-red-500" />
                      <div className="h-3 w-3 rounded-full bg-yellow-500" />
                      <div className="h-3 w-3 rounded-full bg-green-500" />
                    </div>
                    <div className="absolute inset-x-0 text-center text-xs font-medium text-gray-500 dark:text-gray-400">
                      AI Career Assistant
                    </div>
                  </div>
                  <div className="absolute inset-0 mt-12 p-4 space-y-4 z-10">
                    <div className="space-y-3 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg backdrop-blur-sm">
                      <div className="flex items-start">
                        <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-700 flex items-center justify-center mr-3 flex-shrink-0">
                          <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-200" />
                        </div>
                        <div className="text-sm">
                          <p className="text-gray-700 dark:text-gray-200">
                            Tell me about your background and interests in tech and AI...
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg ml-12">
                      <div className="flex items-start">
                        <div className="text-sm">
                          <p className="text-gray-700 dark:text-gray-300">
                            I worked on several ML projects at Berkeley, focusing on LLMs and reinforcement learning. I&apos;m interested in AI systems that can understand natural language...
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg backdrop-blur-sm">
                      <div className="flex items-start">
                        <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-700 flex items-center justify-center mr-3 flex-shrink-0">
                          <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-200" />
                        </div>
                        <div className="text-sm">
                          <p className="text-gray-700 dark:text-gray-200">
                            Great! I found 3 AI startups looking for your specific background. Would you like me to connect you?
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                      <div className="h-10 w-[80%] rounded-full border bg-white dark:bg-gray-900 flex items-center px-4 text-sm text-gray-400">
                        Talk to our AI agent...
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="features" className="py-20 bg-white dark:bg-gray-950">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center mb-12">
              <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 w-fit">
                How It Works
              </div>
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">Your Career on Autopilot</h2>
              <p className="max-w-[800px] text-gray-500 dark:text-gray-400 md:text-xl/relaxed">
                Skip the resume grind and get discovered by AI startups and tech companies
              </p>
            </div>

            <motion.div 
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mt-12"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              {[
                {
                  icon: <MessageSquare className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />,
                  title: "Talk to the Agent",
                  description: "Our AI voice agent calls you and asks smart questions about your background, interests, and goals."
                },
                {
                  icon: <Users className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />,
                  title: "We Build Your Profile",
                  description: "You don't need to write resumes or fill forms. The agent extracts your skills and experiences."
                },
                {
                  icon: <Zap className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />,
                  title: "Real-Time Matching",
                  description: "Our smart backend finds relevant roles and internships at companies looking for your skills."
                },
                {
                  icon: <Award className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />,
                  title: "Get Interview Offers",
                  description: "Instead of applying blindly, you get interview invites from curated companies."
                }
              ].map((feature, i) => (
                <motion.div 
                  key={i} 
                  className="flex flex-col items-center space-y-4 rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 p-6 text-center"
                  variants={fadeIn}
                >
                  <div className="rounded-full bg-indigo-50 dark:bg-indigo-900/20 p-3">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold">{feature.title}</h3>
                  <p className="text-gray-500 dark:text-gray-400">{feature.description}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
        
        {/* Value Proposition */}
        <section id="success-stories" className="py-20 bg-gradient-to-br from-indigo-50 to-white dark:from-gray-900 dark:to-gray-950">
          <div className="container px-4 md:px-6">
            <div className="grid gap-10 lg:grid-cols-2">
              <motion.div 
                className="space-y-6"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 w-fit">
                  Why Students Love Us
                </div>
                <h2 className="text-3xl font-bold">Built for Students, by Students</h2>
                <p className="text-gray-600 dark:text-gray-300">
                  We understand the challenges students face when finding the right opportunities in fast-moving industries like AI and tech.
                </p>
                <div className="space-y-4">
                  {[
                    "Save time: One call, and we handle the rest — profile, matching, outreach.",
                    "Cut through the noise: No more sending 50 applications with no response.",
                    "Early access to AI startups: Get matched with early-stage companies before roles are even posted.",
                    "Built for builders: If you've shipped a project or built something cool, we'll make sure it gets seen."
                  ].map((item, i) => (
                    <div key={i} className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                      <p className="text-gray-600 dark:text-gray-300">{item}</p>
                    </div>
                  ))}
                </div>
                <div className="pt-4">
                  <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank">
                    <Button size="lg" className="group bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
                      Apply Now
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                  </Link>
                </div>
              </motion.div>
              <motion.div
                className="relative h-[400px] lg:h-auto rounded-xl overflow-hidden"
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500 to-purple-600 opacity-20 dark:opacity-30"></div>
                <div className="absolute inset-0 grid grid-cols-2 gap-4 p-6">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <motion.div 
                      key={i}
                      className="rounded-lg bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm p-4 shadow-lg"
                      initial={{ opacity: 0, y: 20 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.1 }}
                      viewport={{ once: true }}
                    >
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-800 flex items-center justify-center">
                          <span className="text-sm font-medium text-indigo-600 dark:text-indigo-300">
                            {String.fromCharCode(65 + i)}
                          </span>
                        </div>
                        <div className="text-sm font-medium">
                          {["Stanford", "Berkeley", "MIT", "CMU"][i]} Student
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        {[
                          "Got connected to 3 AI startups within a week. Already have 2 interviews lined up!",
                          "The AI agent understood exactly what I was looking for. Saved me hours of job hunting.",
                          "I was skeptical at first, but this platform actually works. Found an ML internship I love.",
                          "Being part of this community helped me network with other builders in the AI space."
                        ][i]}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </div>
        </section>
        
        {/* Pricing Section */}
        <section id="pricing" className="py-20 bg-white dark:bg-gray-950">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 w-fit">
                Simple Pricing
              </div>
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                Join Our Exclusive Community
              </h2>
              <p className="max-w-[600px] text-gray-500 dark:text-gray-400 md:text-xl/relaxed">
                Connect with top tech startups and like-minded students
              </p>
            </div>

            <motion.div 
              className="mx-auto max-w-md mt-12"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <div className="rounded-xl border border-indigo-100 dark:border-indigo-800 bg-white dark:bg-gray-900 p-8 shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                  EXCLUSIVE
                </div>
                <div className="flex justify-center">
                  <div className="rounded-full bg-indigo-50 dark:bg-indigo-900/20 p-3">
                    <Sparkles className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-center mt-4">Membership</h3>
                <div className="flex justify-center items-baseline mt-4 mb-6">
                  <span className="text-5xl font-extrabold">$129</span>
                  <span className="text-gray-500 dark:text-gray-400 ml-1">/month</span>
                </div>
                <ul className="space-y-3">
                  {[
                    "Access to AI career agent",
                    "Profile building and matching",
                    "Direct connections with tech startups",
                    "Interview opportunities",
                    "Exclusive community events",
                    "Network with other talented students"
                  ].map((feature, i) => (
                    <li key={i} className="flex">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank" className="w-full">
                    <Button className="w-full bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
                      Apply Now
                    </Button>
                  </Link>
                </div>
                <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-4">
                  Only accepted applicants will be charged
                </p>
              </div>
            </motion.div>
          </div>
        </section>
        
        {/* Application Process */}
        <section className="py-20 bg-gradient-to-br from-indigo-50 to-white dark:from-gray-900 dark:to-gray-950">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center mb-12">
              <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 w-fit">
                How to Join
              </div>
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">The Application Process</h2>
              <p className="max-w-[600px] text-gray-500 dark:text-gray-400 md:text-lg">
                Our community is selective to ensure the highest quality opportunities for our members
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
              {[
                {
                  step: "01",
                  title: "1-Minute Application",
                  description: "Fill out our short application form to tell us about your background and interests.",
                  highlight: "Takes just 60 seconds"
                },
                {
                  step: "02",
                  title: "Selection Process",
                  description: "Our team reviews applications to find talented students, researchers, and builders.",
                  highlight: "Selective acceptance"
                },
                {
                  step: "03",
                  title: "Talent Interview",
                  description: "If selected, you'll have a brief interview with one of our talent recruiters.",
                  highlight: "Get featured on our platform"
                }
              ].map((step, i) => (
                <motion.div 
                  key={i}
                  className="relative border border-gray-100 dark:border-gray-800 rounded-xl p-6 bg-white dark:bg-gray-900"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: i * 0.1 }}
                  viewport={{ once: true }}
                >
                  <div className="absolute -top-3 -left-3 h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
                    {step.step}
                  </div>
                  <h3 className="text-xl font-bold mt-4">{step.title}</h3>
                  <p className="text-gray-500 dark:text-gray-400 mt-2">{step.description}</p>
                  <div className="mt-4 inline-block bg-indigo-50 dark:bg-indigo-900/20 rounded-full px-3 py-1 text-xs font-medium text-indigo-600 dark:text-indigo-300">
                    {step.highlight}
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="mt-12 text-center">
              <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank">
                <Button size="lg" className="group bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white">
                  Start Application
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
        
        {/* CTA Section */}
        <section className="py-20 bg-indigo-600 dark:bg-indigo-700">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <motion.div 
                className="space-y-2"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-white">
                  Ready to Launch Your Career?
                </h2>
                <p className="max-w-[600px] text-indigo-100 md:text-xl/relaxed">
                  Join our exclusive community of talented students and connect with top tech startups.
                </p>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                viewport={{ once: true }}
              >
                <Link href="https://docs.google.com/forms/d/1nK9EPoqgmn4q2mpD5Q53IZR29J3oAP1mOupAw292Oo4/edit" target="_blank">
                  <Button size="lg" className="group bg-white text-indigo-600 hover:bg-indigo-50">
                    Apply Now
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
              </motion.div>
            </div>
          </div>
        </section>
      </main>
      <Footer />

      <style jsx global>{`
        .bg-grid-pattern {
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill-rule='evenodd'%3E%3Cg fill='%234f46e5' fill-opacity='0.1'%3E%3Cpath opacity='.5' d='M96 95h4v1h-4v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4h-9v4h-1v-4H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15v-9H0v-1h15V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h9V0h1v15h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9h4v1h-4v9zm-1 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm9-10v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-10 0v-9h-9v9h9zm-9-10h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9zm10 0h9v-9h-9v9z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
      `}</style>
    </div>
  )
}