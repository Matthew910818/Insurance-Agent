import { Coffee } from 'lucide-react';
import { motion } from 'framer-motion';

export function BuyMeCoffee() {
  const COFFEE_URL = 'https://buy.stripe.com/5kA176bA895ggog4gh';

  return (
    <motion.a
      href={COFFEE_URL}
      target="_blank"
      rel="noopener noreferrer"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="hidden sm:flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-full text-sm font-medium transition-colors shadow-subtle hover:shadow-hover"
    >
      <Coffee className="h-4 w-4" />
      <span>Buy Me a Coffee</span>
    </motion.a>
  );
}