import { Link } from "react-router-dom";
import manifest from "../config/features.generated.json";
import { ArrowRight, CheckCircle } from "lucide-react";

const features: Feature[] = manifest.items;

export default function LandingPage() {
  return (
    <div className="bg-bg text-white min-h-screen flex flex-col">
      {/* Hero */}
      <section className="bg-bg px-6 py-16 md:py-24">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Decision-making for communities, done right.
          </h1>
          <p className="text-lg md:text-xl text-muted mb-8">
            The Commons is a place where people decide together — in the open, in real time,
            without the noise of politics as usual.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/auth"
              className="bg-primary text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary/90 transition"
            >
              Get Started
            </Link>
            <a
              href="#philosophy"
              className="border border-primary text-primary px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary/10 transition"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Summary / System Goals */}
      <section className="px-6 py-16 bg-surface">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xl leading-relaxed">
            The Commons is a democratic decision-making platform. It's built for communities that want clarity,
            transparency, and participation — without drowning in bureaucracy. You can propose, discuss, vote,
            and delegate in one place, and see results as they happen.
          </p>
        </div>
      </section>

      {/* Philosophy */}
      <section id="philosophy" className="px-6 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-semibold mb-6">Philosophy</h2>
          <p className="text-lg text-muted leading-relaxed">
            Decisions are better when they're made in the open. Delegation is there for efficiency, not to remove your say.
            Every member has the same weight in the process. Transparency isn't an add-on — it's the default.
          </p>
          <p className="text-lg text-muted leading-relaxed mt-4">
            The Commons is shaped by the idea that democracy should be simple enough to understand,
            fast enough to act, and honest enough to trust. It's a tool, not a boss.
          </p>
        </div>
      </section>

      {/* Basic Functions */}
      <section className="px-6 py-16 bg-surface">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-semibold mb-8">Basic Functions</h2>
          <ul className="space-y-4">
            {[
              "Propose new ideas or changes",
              "Vote directly, or delegate your vote to someone you trust",
              "Discuss and comment on proposals",
              "See live results as decisions are made",
              "Track community activity and participation",
            ].map((item, idx) => (
              <li key={idx} className="flex items-start">
                <CheckCircle className="text-primary mr-3 mt-1" size={20} />
                <span className="text-lg">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Current Features */}
      <section className="px-6 py-16">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-semibold mb-8">Current Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, idx) => (
              <div key={idx} className="bg-surface p-6 rounded-lg border border-border hover:border-primary transition">
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Getting Started */}
      <section className="px-6 py-16 bg-surface">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-semibold mb-6">Getting Started</h2>
          <ol className="text-lg text-left space-y-3 max-w-md mx-auto">
            <li>1. Create an account</li>
            <li>2. Join your community</li>
            <li>3. Propose, vote, and delegate</li>
            <li>4. See results live</li>
          </ol>
          <Link
            to="/auth"
            className="inline-flex items-center mt-8 bg-primary text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary/90 transition"
          >
            Get Started <ArrowRight className="ml-2" size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 bg-bg border-t border-border text-center text-muted text-sm">
        © {new Date().getFullYear()} The Commons — Open Source Democracy Platform
      </footer>
    </div>
  );
}
