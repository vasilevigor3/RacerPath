import * as React from 'react';
import { cn } from '@/lib/utils';

const Avatar = React.forwardRef(({ className, ...props }, ref) =>
  React.createElement('div', {
    ref,
    className: cn(
      'relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full border-2 border-border bg-muted ring-2 ring-background',
      className
    ),
    ...props,
  })
);
Avatar.displayName = 'Avatar';

const AvatarImage = React.forwardRef(({ className, ...props }, ref) =>
  React.createElement('img', {
    ref,
    className: cn('aspect-square h-full w-full object-cover', className),
    ...props,
  })
);
AvatarImage.displayName = 'AvatarImage';

const AvatarFallback = React.forwardRef(({ className, ...props }, ref) =>
  React.createElement('div', {
    ref,
    className: cn(
      'flex h-full w-full items-center justify-center rounded-full bg-primary/20 text-sm font-semibold text-primary',
      className
    ),
    ...props,
  })
);
AvatarFallback.displayName = 'AvatarFallback';

export { Avatar, AvatarImage, AvatarFallback };
