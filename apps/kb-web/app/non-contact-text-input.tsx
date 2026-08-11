"use client";

import { InputHTMLAttributes, useState } from "react";

type Props = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "autoComplete" | "autoCorrect" | "autoCapitalize" | "spellCheck"
>;

/**
 * Text input that resists macOS Contact AutoFill without honeypot fields
 * (honeypots were rendering as extra underline inputs in Safari).
 */
export function NonContactTextInput(props: Props) {
  const [locked, setLocked] = useState(true);

  return (
    <input
      {...props}
      type={props.type ?? "text"}
      readOnly={locked}
      autoComplete="one-time-code"
      autoCorrect="off"
      autoCapitalize="off"
      spellCheck={false}
      data-1p-ignore
      data-lpignore="true"
      data-bwignore="true"
      data-form-type="other"
      onFocus={(e) => {
        setLocked(false);
        e.currentTarget.removeAttribute("readonly");
        props.onFocus?.(e);
      }}
      onBlur={(e) => {
        setLocked(true);
        props.onBlur?.(e);
      }}
    />
  );
}
