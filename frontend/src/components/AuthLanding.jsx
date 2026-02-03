import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const AuthLanding = () => (
  <section id="auth" className="section auth-landing reveal" data-auth-only>
    <div className="auth-hero">
      <div>
        <p className="eyebrow text-primary font-medium text-sm uppercase tracking-widest">Start here</p>
        <h1 className="text-foreground font-bold tracking-tight">
          <span className="text-[var(--countdown-color)]">Sign in</span>
          {' '}
          to your private racing cabinet.
        </h1>
        <p className="lead text-muted-foreground mt-2 max-w-lg">
          Create an account, log in, and unlock your personal dashboard with tasks, events, and readiness stats.
        </p>
      </div>
      <div className="auth-card grid gap-5">
        <Card className="border-border shadow-lg shadow-black/20">
          <CardHeader className="pb-4">
            <CardTitle className="text-base font-semibold text-foreground">Create account</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <form data-register-form className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="registerLogin">Login</Label>
                <Input id="registerLogin" name="registerLogin" autoComplete="username" placeholder="igor" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="registerEmail">Email</Label>
                <Input id="registerEmail" name="registerEmail" type="email" autoComplete="email" placeholder="igor@mail.com" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="registerPassword">Password</Label>
                <Input
                  id="registerPassword"
                  name="registerPassword"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Create a password"
                />
              </div>
              <Button type="submit" className="w-full mt-1">
                Register
              </Button>
              <p className="form-status text-sm text-muted-foreground min-h-[1.25rem]" data-register-status>
                &nbsp;
              </p>
            </form>
          </CardContent>
        </Card>
        <Card className="border-border shadow-lg shadow-black/20">
          <CardHeader className="pb-4">
            <CardTitle className="text-base font-semibold text-foreground">Login</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <form data-login-form className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="loginEmail">Email</Label>
                <Input id="loginEmail" name="loginEmail" type="email" autoComplete="email" placeholder="you@mail.com" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="loginPassword">Password</Label>
                <Input id="loginPassword" name="loginPassword" type="password" autoComplete="current-password" placeholder="Your password" />
              </div>
              <Button type="submit" className="w-full mt-1">
                Login
              </Button>
              <p className="form-status text-sm text-muted-foreground min-h-[1.25rem]" data-login-status>
                Not logged in.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  </section>
);

export default AuthLanding;
