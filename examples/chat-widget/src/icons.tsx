import React from "react";

type IconProps = React.SVGProps<SVGSVGElement>;

function Svg(props: IconProps) {
  // 默认 1em × 1em；className（如 Tailwind 的 w-5 h-5）覆盖到 size，业务方接 Tailwind 后即可控大小。
  // 本 demo 无 Tailwind 时 1em 等于父级 font-size，撑得不大不致撑爆容器。
  const { className, ...rest } = props;
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      className={className}
      {...rest}
    />
  );
}

export function SendIcon(props: IconProps) {
  return (
    <Svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M3.4 20.4l17.45-7.48a1 1 0 0 0 0-1.84L3.4 3.6a1 1 0 0 0-1.39 1.21L4.5 11 14 12l-9.5 1-2.49 6.19a1 1 0 0 0 1.39 1.21z" />
    </Svg>
  );
}

export function BotIcon(props: IconProps) {
  return (
    <Svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4M8 16h.01M16 16h.01" />
    </Svg>
  );
}

export function UserIcon(props: IconProps) {
  return (
    <Svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </Svg>
  );
}

export function XIcon(props: IconProps) {
  return (
    <Svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M18 6L6 18M6 6l12 12" />
    </Svg>
  );
}