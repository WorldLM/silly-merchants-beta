// Generate answers for questions based on business data
export function getAnswerForQuestion(question, businessData) {
  const {
    businessIdea,
    problemSolution,
    valueProposition,
    teamBackground,
    fundingUsage,
    teamCulture
  } = businessData;
  
  // First 100 customers question
  if (question.includes('first 100 customers')) {
    return `Absolutely! We're taking a three-pronged approach to customer acquisition. First, we're leveraging ${
      businessIdea.includes('AI') 
        ? 'AI industry partnerships with companies that already serve our target market' 
        : 'strategic partnerships with established players in the space'
    }. Second, we're implementing highly targeted content marketing focused on the specific pain points we solve. And third, we're running limited-time pilot programs that allow customers to experience the value with minimal risk. Our early tests show that ${
      businessIdea.includes('platform') 
        ? 'our platform demos convert at nearly 35% when we can get in front of the right decision-maker' 
        : 'direct outreach to decision-makers is yielding a 28% meeting conversion rate'
    }. We're confident we can reach our first 100 customers within 6 months of launch.`;
  } 
  
  // CAC and LTV question
  else if (question.includes('acquisition cost') || question.includes('lifetime value')) {
    return `Great question about unit economics. Our current CAC is projected at $${
      businessIdea.includes('enterprise') ? '2,800' : '950'
    } per customer, which we expect to decrease by about 30% as we optimize our funnel. On the LTV side, our ${
      businessIdea.includes('subscription') || businessIdea.includes('SaaS') 
        ? 'subscription model' 
        : 'revenue model'
    } projects an average customer lifetime of ${
      businessIdea.includes('enterprise') ? '36' : '24'
    } months with an average monthly value of $${
      businessIdea.includes('enterprise') ? '1,200' : '350'
    }. This gives us an LTV of approximately $${
      businessIdea.includes('enterprise') ? '43,200' : '8,400'
    }, and an LTV:CAC ratio of ${
      businessIdea.includes('enterprise') ? '15:1' : '8.8:1'
    }, which is well above the industry benchmark of 3:1.`;
  }
  
  // ... other question types
  
  // Default response for other questions
  return `That's an excellent question. Based on our market research and early customer feedback, we've developed a solution that addresses this specific need in a unique way. Our approach combines innovative technology with deep industry expertise, allowing us to deliver exceptional value to our customers. We've validated this with early adopters who are seeing significant improvements in their operations and outcomes.`;
}

// Generate judge responses based on business data
export function generateJudgeResponses(businessData, judges) {
  const {
    businessIdea,
    problemSolution,
    valueProposition,
    teamBackground,
    fundingUsage,
    teamCulture
  } = businessData;
  
  return [
    {
      judge: judges[0].name,
      score: businessIdea.includes('AI') ? 8 : valueProposition.length > 100 ? 7 : 6,
      investment: businessIdea.includes('AI') ? "$300,000" : valueProposition.length > 100 ? "$200,000" : "$150,000",
      feedback: `I'm genuinely impressed with your ${
        businessIdea.includes('AI') 
          ? 'innovative use of AI technology to solve a real market need' 
          : 'approach to tackling this significant market opportunity'
      }. Your ${
        valueProposition.includes('reduces costs') 
          ? 'cost reduction metrics are compelling' 
          : 'value proposition is clearly articulated'
      } and I can see the potential for rapid growth. What particularly stood out to me was your ${
        teamBackground.includes('Google') || teamBackground.includes('Meta') 
          ? 'exceptional team background from top tech companies' 
          : 'thoughtful go-to-market strategy'
      }. However, I'd like to see more detail on your ${
        businessIdea.includes('platform') 
          ? 'platform defensibility against larger competitors' 
          : 'customer acquisition strategy and unit economics'
      }. Overall, I'm excited about your potential and would like to support your journey.`
    },
    // ... other judge responses
  ];
} 