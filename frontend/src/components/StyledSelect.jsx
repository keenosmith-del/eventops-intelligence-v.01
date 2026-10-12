import {
  Children,
  useEffect,
  useLayoutEffect,
  useId,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown } from "lucide-react";
import "../controls.css";

// A consistent rounded picker, including its menu, across desktop and mobile.
export default function StyledSelect({
  id,
  value,
  onChange,
  disabled,
  children,
  ...props
}) {
  const uid = useId();

  const triggerId = id || `select-${uid}`;

  const menuId = `${triggerId}-options`;

  const options = Children.toArray(children).map((option) => ({
    value: String(option.props.value ?? option.props.children),
    label: option.props.children,
    disabled: Boolean(option.props.disabled),
  }));

  const selected = options.findIndex(
    (option) => option.value === String(value),
  );

  const [open, setOpen] = useState(false);

  const [active, setActive] = useState(Math.max(0, selected));

  const [position, setPosition] = useState(null);

  const button = useRef(null),
    menu = useRef(null);

  const typeahead = useRef({ text: "", time: 0 });

  useLayoutEffect(() => {
    if (!open || disabled) return;
    function place() {
      const rect = button.current.getBoundingClientRect();

      const height = window.innerHeight;

      const below = height - rect.bottom - 16;

      const above = rect.top - 16;

      const upward =
        below < Math.min(240, options.length * 40 + 16) && above > below;

      const width = Math.min(Math.max(rect.width, 180), window.innerWidth - 24);

      setPosition({
        left: Math.max(12, Math.min(rect.left, window.innerWidth - width - 12)),
        width,
        maxHeight: Math.max(80, Math.min(280, upward ? above : below)),
        ...(upward
          ? { bottom: height - rect.top + 8 }
          : { top: rect.bottom + 8 }),
      });
    }

    function dismiss(event) {
      if (
        !button.current?.contains(event.target) &&
        !menu.current?.contains(event.target)
      )
        setOpen(false);
    }

    place();

    const observer = new ResizeObserver(place);

    observer.observe(button.current);

    window.addEventListener("resize", place);

    window.addEventListener("scroll", place, true);

    document.addEventListener("pointerdown", dismiss);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
      document.removeEventListener("pointerdown", dismiss);
    };
  }, [open, disabled, options.length]);

  useEffect(() => {
    if (open)
      menu.current
        ?.querySelector(`[data-index="${active}"]`)
        ?.scrollIntoView({ block: "nearest" });
  }, [active, open, position?.maxHeight]);

  function choose(index) {
    if (!options[index] || options[index].disabled) return;
    onChange({ target: { value: options[index].value } });
    setOpen(false);
    button.current?.focus({ preventScroll: true });
  }

  function move(direction) {
    let next = active;
    for (let i = 0; i < options.length; i++) {
      next = (next + direction + options.length) % options.length;
      if (!options[next].disabled) {
        setActive(next);
        break;
      }
    }
  }

  return (
    <span className="select-control">
      <button
        {...props}
        ref={button}
        id={triggerId}
        type="button"
        role="combobox"
        className="styled-select"
        value={value}
        disabled={disabled}
        aria-expanded={open && !disabled}
        aria-haspopup="listbox"
        aria-controls={open ? menuId : undefined}
        aria-activedescendant={open ? `${menuId}-${active}` : undefined}
        onClick={() => {
          setActive(Math.max(0, selected));
          setOpen((current) => !current);
        }}
        onBlur={(event) => {
          if (!menu.current?.contains(event.relatedTarget)) setOpen(false);
        }}
        onKeyDown={(event) => {
          if (
            ["ArrowDown", "ArrowUp", "Home", "End", "Enter", " "].includes(
              event.key,
            )
          ) {
            event.preventDefault();
            if (!open) {
              setActive(
                event.key === "Home"
                  ? options.findIndex((option) => !option.disabled)
                  : event.key === "End"
                    ? options.findLastIndex((option) => !option.disabled)
                    : Math.max(0, selected),
              );
              setOpen(true);
            } else if (event.key === "Enter" || event.key === " ")
              choose(active);
            else if (event.key === "Home")
              setActive(options.findIndex((option) => !option.disabled));
            else if (event.key === "End")
              setActive(options.findLastIndex((option) => !option.disabled));
            else move(event.key === "ArrowDown" ? 1 : -1);
          } else if (event.key === "Escape") {
            event.preventDefault();
            setOpen(false);
          } else if (event.key === "Tab") setOpen(false);
          else if (
            event.key.length === 1 &&
            !event.ctrlKey &&
            !event.metaKey &&
            !event.altKey
          ) {
            const now = Date.now();

            const text =
              (now - typeahead.current.time < 600
                ? typeahead.current.text
                : "") + event.key.toLowerCase();

            typeahead.current = { text, time: now };

            const index = options.findIndex(
              (option) =>
                !option.disabled &&
                String(option.label).toLowerCase().startsWith(text),
            );

            if (index >= 0) {
              event.preventDefault();
              setActive(index);
              setOpen(true);
            }
          }
        }}
      >
        <span>{options[selected]?.label ?? "Select an option"}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>
      {open &&
        !disabled &&
        position &&
        createPortal(
          <div
            ref={menu}
            id={menuId}
            role="listbox"
            aria-labelledby={triggerId}
            className="eventops-select-menu"
            style={position}
          >
            {options.map((option, index) => (
              <div
                key={option.value}
                id={`${menuId}-${index}`}
                role="option"
                aria-selected={index === selected}
                aria-disabled={option.disabled || undefined}
                data-index={index}
                className={`select-option ${index === active ? "is-active" : ""}`}
                onPointerDown={(event) => event.preventDefault()}
                onPointerMove={() => {
                  if (!option.disabled) setActive(index);
                }}
                onClick={() => choose(index)}
              >
                <span>{option.label}</span>
                {index === selected && <Check size={14} aria-hidden="true" />}
              </div>
            ))}
          </div>,
          document.body,
        )}
    </span>
  );
}
