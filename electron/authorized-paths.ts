import * as fs from 'fs';
import * as path from 'path';

export class AuthorizedPaths {
  private readonly roots = new Set<string>();

  authorize(dirPath: string): void {
    const canonical = this.resolveCanonical(dirPath);
    this.roots.add(canonical);
  }

  deauthorize(dirPath: string): void {
    const canonical = this.resolveCanonical(dirPath);
    this.roots.delete(canonical);
  }

  getAuthorizedRoots(): string[] {
    return Array.from(this.roots);
  }

  isPathAllowed(targetPath: string): boolean {
    if (this.roots.size === 0) return false;
    let canonical: string;
    try {
      canonical = this.resolveCanonical(targetPath);
    } catch {
      return false;
    }
    for (const root of this.roots) {
      if (canonical === root || canonical.startsWith(root + path.sep)) {
        return true;
      }
    }
    return false;
  }

  private resolveCanonical(inputPath: string): string {
    const resolved = path.resolve(inputPath);
    if (fs.existsSync(resolved)) {
      return fs.realpathSync(resolved);
    }
    const parentDir = path.dirname(resolved);
    const parentReal = fs.realpathSync(parentDir);
    return path.join(parentReal, path.basename(resolved));
  }
}

export const authorizedPaths = new AuthorizedPaths();
