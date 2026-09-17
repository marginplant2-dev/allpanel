import { LifeBuoy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const FAQ = [
  {
    q: "Is this real-money gambling?",
    a: "No. SportX uses virtual/demo credits only and is an entertainment simulation. There is no real payment processing or real wagering.",
  },
  {
    q: "How do I get virtual credits?",
    a: "Send a Deposit request from your Wallet page — it goes to your agent or admin for approval, and virtual credits are added once approved. You can also request a Withdraw to send credits back to your agent's pool.",
  },
  {
    q: "How do live events work?",
    a: "Live events display scores and status in real time. This is a display-only experience powered by the platform's data providers.",
  },
  {
    q: "Who can I contact for support?",
    a: "Reach out to the administrator or agent who manages your account for any assistance.",
  },
];

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-2">
        <LifeBuoy className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">Help & Support</h1>
      </div>

      <div className="space-y-4">
        {FAQ.map((item) => (
          <Card key={item.q}>
            <CardHeader>
              <CardTitle className="text-base">{item.q}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{item.a}</CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
