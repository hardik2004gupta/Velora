import { Github, Linkedin } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/40 px-5 py-2.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground/40">
          Designed &amp; Engineered by{" "}
          <span className="font-medium text-muted-foreground/60">Hardik Gupta</span>
        </span>
        <div className="flex items-center gap-2.5">
          <Link
            href="https://github.com/hardik2004gupta"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground/30 hover:text-muted-foreground transition-colors"
          >
            <Github className="h-3.5 w-3.5" />
          </Link>
          <Link
            href="https://www.linkedin.com/in/hardikgupta2004/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground/30 hover:text-muted-foreground transition-colors"
          >
            <Linkedin className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </footer>
  );
}
