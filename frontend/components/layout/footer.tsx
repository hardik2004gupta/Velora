import { Github, Linkedin, Cpu } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-card/30 px-6 py-4">
      <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Cpu className="h-3.5 w-3.5 text-velora-400" />
          <span>
            Designed &amp; Engineered by{" "}
            <span className="font-semibold text-foreground">Hardik Gupta</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="https://github.com/hardik2004gupta"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Github className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">hardik2004gupta</span>
          </Link>
          <Link
            href="https://www.linkedin.com/in/hardikgupta2004/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Linkedin className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">hardikgupta2004</span>
          </Link>
        </div>
      </div>
    </footer>
  );
}
